import os

AUTOMATION_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(AUTOMATION_ROOT, "output", "step1_anilist")
ANILIST_URL = "https://graphql.anilist.co"
ID_CHUNK_SIZE = 5000
PER_PAGE = 50

MAX_ID_QUERY = """
query {
  Page(page: 1, perPage: 1) {
    media(type: ANIME, sort: ID_DESC) {
      id
    }
  }
}
"""

CHUNK_PAGE_QUERY = """
query ($page: Int, $perPage: Int, $idIn: [Int]) {
  Page(page: $page, perPage: $perPage) {
    pageInfo { hasNextPage lastPage }
    media(id_in: $idIn, type: ANIME, sort: ID) {
      id
      idMal
      updatedAt
      title { romaji english native userPreferred }
      format
      status
      episodes
      nextAiringEpisode { episode }
      popularity
    }
  }
}
"""

INCREMENTAL_PAGE_QUERY = """
query ($page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    pageInfo { hasNextPage lastPage }
    media(type: ANIME, sort: UPDATED_AT_DESC) {
      id
      idMal
      updatedAt
      title { romaji english native userPreferred }
      format
      status
      episodes
      nextAiringEpisode { episode }
      popularity
    }
  }
}
"""
