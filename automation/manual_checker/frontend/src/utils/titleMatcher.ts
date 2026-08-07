import { pipeline, env } from '@xenova/transformers';

// Configure transformers to use the browser cache and avoid local file system
env.allowLocalModels = false;
env.useBrowserCache = true;

let extractorPromise: Promise<any> | null = null;
let extractor: any = null;

/**
 * Initializes the MiniLM model for feature extraction.
 */
async function initExtractor() {
  if (!extractorPromise) {
    extractorPromise = pipeline('feature-extraction', 'Xenova/all-MiniLM-L6-v2', {
      quantized: true,
    });
  }
  extractor = await extractorPromise;
  return extractor;
}

function normalizeTitle(s: string): string {
  return (s || '').toLowerCase().replace(/[^a-z0-9 ]/g, '');
}

function extractNumbers(s: string): string {
  return s.match(/\d+/g)?.join('') || '';
}

function cosineSimilarity(vecA: Float32Array, vecB: Float32Array): number {
  let dotProduct = 0.0;
  let normA = 0.0;
  let normB = 0.0;
  for (let i = 0; i < vecA.length; i++) {
    dotProduct += vecA[i] * vecB[i];
    normA += vecA[i] * vecA[i];
    normB += vecB[i] * vecB[i];
  }
  if (normA === 0 || normB === 0) return 0;
  return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
}

export async function getEmbeddings(titles: string[]): Promise<Float32Array[]> {
  const ext = await initExtractor();
  const embeddings: Float32Array[] = [];
  
  // Process in chunks to prevent UI blocking and OOM
  const chunkSize = 50;
  for (let i = 0; i < titles.length; i += chunkSize) {
    const chunk = titles.slice(i, i + chunkSize);
    const out = await ext(chunk, { pooling: 'mean', normalize: true });
    
    const dim = out.dims[1];
    for (let j = 0; j < chunk.length; j++) {
      const slice = new Float32Array(out.data.buffer, out.data.byteOffset + j * dim * 4, dim);
      embeddings.push(slice);
    }
  }
  
  return embeddings;
}

/**
 * Batch-evaluates all episodes using a local embedding model.
 */
export async function batchMatchTitles(
  titles1: string[],
  titles2: string[]
): Promise<boolean[]> {
  const results = new Array(titles1.length).fill(false);
  const toEmbed1: { idx: number; title: string }[] = [];
  const toEmbed2: { idx: number; title: string }[] = [];

  for (let i = 0; i < titles1.length; i++) {
    const s1 = normalizeTitle(titles1[i]);
    const s2 = normalizeTitle(titles2[i]);

    if (s1.trim().length === 0 || s2.trim().length === 0) {
      results[i] = false;
      continue;
    }

    if (s1 === s2) {
      results[i] = true;
      continue;
    }

    const num1 = extractNumbers(titles1[i]);
    const num2 = extractNumbers(titles2[i]);
    if (num1 !== num2) {
      results[i] = false;
      continue;
    }

    toEmbed1.push({ idx: i, title: s1 });
    toEmbed2.push({ idx: i, title: s2 });
  }

  if (toEmbed1.length > 0) {
    const embs1 = await getEmbeddings(toEmbed1.map(x => x.title));
    const embs2 = await getEmbeddings(toEmbed2.map(x => x.title));

    for (let k = 0; k < toEmbed1.length; k++) {
      const sim = cosineSimilarity(embs1[k], embs2[k]);
      // Threshold of 0.8 is highly robust for MiniLM normalized embeddings
      results[toEmbed1[k].idx] = sim >= 0.8; 
    }
  }

  return results;
}

