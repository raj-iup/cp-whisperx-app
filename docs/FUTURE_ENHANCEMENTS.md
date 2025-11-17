# Future Enhancements for Soundtrack Enrichment

This document outlines potential improvements to the soundtrack enrichment system, explaining what each enhancement is, why it's valuable, and how it could be implemented.

---

## 1. MusicBrainz API Integration

### What It Is
[MusicBrainz](https://musicbrainz.org) is an open-source music encyclopedia that collects music metadata. It has comprehensive data about songs, albums, artists, and relationships between them.

### Why It's Valuable
- **Free and Open**: No API key required for non-commercial use
- **Comprehensive**: Contains soundtrack information for many Bollywood movies
- **Structured Data**: Well-organized with relationships (movie → album → tracks → artists)
- **Community Maintained**: Active community keeps data up-to-date
- **No Manual Entry**: Eliminates need to manually add each movie's soundtrack

### How to Implement

#### Architecture
```
TMDB Stage (Stage 2)
    ↓
Get IMDb ID from TMDB
    ↓
Query MusicBrainz for soundtrack album using IMDb ID
    ↓
Fetch all tracks, artists, composers
    ↓
Save to enrichment.json
```

#### Implementation Steps

**Step 1: Add MusicBrainz Client**
```python
# File: scripts/musicbrainz_client.py

import musicbrainzngs
from typing import List, Dict, Optional

# Configure client
musicbrainzngs.set_useragent(
    "CP-WhisperX-App",
    "1.0",
    "your-email@example.com"
)

def search_soundtrack_by_imdb(imdb_id: str) -> Optional[Dict]:
    """
    Search for movie soundtrack using IMDb ID
    
    Args:
        imdb_id: IMDb identifier (e.g., 'tt0473367')
    
    Returns:
        Soundtrack album data or None
    """
    try:
        # Search for releases linked to this IMDb ID
        result = musicbrainzngs.browse_releases(
            inc=['recordings', 'artist-credits'],
            imdb=imdb_id,
            release_type=['soundtrack']
        )
        
        if result.get('release-list'):
            return result['release-list'][0]
        return None
    except Exception as e:
        print(f"MusicBrainz search error: {e}")
        return None


def get_soundtrack_tracks(release_id: str) -> List[Dict[str, str]]:
    """
    Get all tracks from a soundtrack release
    
    Args:
        release_id: MusicBrainz release ID
    
    Returns:
        List of tracks with title, artist, composer
    """
    try:
        release = musicbrainzngs.get_release_by_id(
            release_id,
            includes=['recordings', 'artist-credits', 'work-rels']
        )
        
        tracks = []
        for medium in release['release'].get('medium-list', []):
            for track in medium.get('track-list', []):
                recording = track.get('recording', {})
                
                # Get track title
                title = recording.get('title', '')
                
                # Get artists
                artist_credits = recording.get('artist-credit', [])
                artists = []
                for credit in artist_credits:
                    if isinstance(credit, dict):
                        artists.append(credit.get('artist', {}).get('name', ''))
                artist_str = ', '.join(artists)
                
                # Get composer (from work relationships)
                composer = ''
                work_relations = recording.get('work-relation-list', [])
                for relation in work_relations:
                    if relation.get('type') == 'composer':
                        composer = relation.get('target', '')
                        break
                
                tracks.append({
                    'title': title,
                    'artist': artist_str,
                    'composer': composer
                })
        
        return tracks
    except Exception as e:
        print(f"MusicBrainz tracks error: {e}")
        return []
```

**Step 2: Integrate into TMDB Enrichment**
```python
# File: scripts/tmdb_enrichment.py

from scripts.musicbrainz_client import search_soundtrack_by_imdb, get_soundtrack_tracks

def get_soundtrack_for_movie(
    title: str,
    year: Optional[int],
    imdb_id: Optional[str] = None,
    soundtrack_db: Optional[Dict] = None,
    use_musicbrainz: bool = True  # New parameter
) -> List[Dict[str, str]]:
    """Enhanced version with MusicBrainz support"""
    
    # First, try local database (fastest)
    if soundtrack_db:
        local_tracks = try_local_database(title, year, imdb_id, soundtrack_db)
        if local_tracks:
            return local_tracks
    
    # If not found and we have IMDb ID, try MusicBrainz
    if use_musicbrainz and imdb_id:
        logger.info(f"Querying MusicBrainz for soundtrack (IMDb: {imdb_id})")
        
        soundtrack_album = search_soundtrack_by_imdb(imdb_id)
        if soundtrack_album:
            release_id = soundtrack_album.get('id')
            tracks = get_soundtrack_tracks(release_id)
            
            if tracks:
                logger.info(f"✓ Found {len(tracks)} tracks from MusicBrainz")
                
                # Optionally cache to local database
                cache_to_local_db(title, year, imdb_id, tracks)
                
                return tracks
        else:
            logger.info("No soundtrack found in MusicBrainz")
    
    return []
```

**Step 3: Add Configuration**
```python
# In shared/config.py
class PipelineConfig(BaseSettings):
    # Soundtrack settings
    use_musicbrainz: bool = Field(default=True, env="USE_MUSICBRAINZ")
    cache_musicbrainz: bool = Field(default=True, env="CACHE_MUSICBRAINZ")
```

#### Pros & Cons

**Pros:**
- ✅ Automatic soundtrack data for most movies
- ✅ No manual data entry required
- ✅ Free and open source
- ✅ High-quality, community-verified data
- ✅ Can cache results to local database

**Cons:**
- ❌ Requires internet connection
- ❌ Rate limited (1 request per second)
- ❌ Not all Bollywood movies have complete data
- ❌ Adds external dependency

---

## 2. Spotify API Integration

### What It Is
[Spotify Web API](https://developer.spotify.com/documentation/web-api/) provides access to Spotify's music catalog, including albums, tracks, artists, and audio features.

### Why It's Valuable
- **Comprehensive Catalog**: Nearly all Bollywood soundtracks available
- **Rich Metadata**: Artist names, album info, release dates
- **Audio Features**: Tempo, key, energy (useful for lyrics detection)
- **Popularity Data**: Can prioritize popular songs
- **High Quality**: Professional metadata curation

### How to Implement

#### Architecture
```
TMDB Stage
    ↓
Get movie title + year
    ↓
Search Spotify for soundtrack album
    ↓
Fetch tracks + audio features
    ↓
Enrich with popularity and audio metadata
    ↓
Save to enrichment.json
```

#### Implementation Steps

**Step 1: Spotify Client Setup**
```python
# File: scripts/spotify_client.py

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from typing import List, Dict, Optional

class SpotifyClient:
    """Client for fetching soundtrack data from Spotify"""
    
    def __init__(self, client_id: str, client_secret: str):
        """
        Initialize Spotify client
        
        Args:
            client_id: Spotify app client ID
            client_secret: Spotify app client secret
        """
        auth_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        self.sp = spotipy.Spotify(auth_manager=auth_manager)
    
    def search_soundtrack(
        self,
        movie_title: str,
        year: Optional[int] = None
    ) -> Optional[str]:
        """
        Search for movie soundtrack album
        
        Args:
            movie_title: Movie title
            year: Release year
        
        Returns:
            Album ID or None
        """
        # Build search query
        query = f'album:"{movie_title}" soundtrack'
        if year:
            query += f' year:{year}'
        
        try:
            results = self.sp.search(q=query, type='album', limit=5)
            albums = results['albums']['items']
            
            # Filter for exact matches
            for album in albums:
                album_name = album['name'].lower()
                if movie_title.lower() in album_name:
                    return album['id']
            
            # Return first result if no exact match
            return albums[0]['id'] if albums else None
            
        except Exception as e:
            print(f"Spotify search error: {e}")
            return None
    
    def get_album_tracks(
        self,
        album_id: str,
        include_audio_features: bool = False
    ) -> List[Dict]:
        """
        Get all tracks from an album
        
        Args:
            album_id: Spotify album ID
            include_audio_features: Whether to fetch audio features
        
        Returns:
            List of tracks with metadata
        """
        try:
            # Get album details
            album = self.sp.album(album_id)
            
            tracks = []
            for item in album['tracks']['items']:
                track_data = {
                    'title': item['name'],
                    'artist': ', '.join([a['name'] for a in item['artists']]),
                    'duration_ms': item['duration_ms'],
                    'track_number': item['track_number'],
                    'popularity': None,
                    'spotify_id': item['id']
                }
                
                # Get additional track details (includes popularity)
                track_full = self.sp.track(item['id'])
                track_data['popularity'] = track_full.get('popularity', 0)
                
                # Optionally get audio features
                if include_audio_features:
                    features = self.sp.audio_features(item['id'])[0]
                    if features:
                        track_data['audio_features'] = {
                            'tempo': features['tempo'],
                            'energy': features['energy'],
                            'danceability': features['danceability'],
                            'valence': features['valence'],
                            'key': features['key'],
                            'mode': features['mode']
                        }
                
                tracks.append(track_data)
            
            return tracks
            
        except Exception as e:
            print(f"Spotify tracks error: {e}")
            return []
    
    def get_soundtrack_with_metadata(
        self,
        movie_title: str,
        year: Optional[int] = None
    ) -> Dict:
        """
        Get complete soundtrack with rich metadata
        
        Returns:
            Dict with album info and tracks
        """
        album_id = self.search_soundtrack(movie_title, year)
        
        if not album_id:
            return {'found': False, 'tracks': []}
        
        tracks = self.get_album_tracks(album_id, include_audio_features=True)
        
        return {
            'found': True,
            'album_id': album_id,
            'tracks': tracks,
            'source': 'spotify'
        }
```

**Step 2: Integration**
```python
# File: scripts/tmdb_enrichment.py

from scripts.spotify_client import SpotifyClient

def get_soundtrack_for_movie(
    title: str,
    year: Optional[int],
    imdb_id: Optional[str] = None,
    soundtrack_db: Optional[Dict] = None,
    use_spotify: bool = True,
    spotify_client: Optional[SpotifyClient] = None
) -> List[Dict[str, str]]:
    """Enhanced with Spotify support"""
    
    # Try local database first
    # ... (existing code)
    
    # Try Spotify if enabled
    if use_spotify and spotify_client:
        logger.info(f"Querying Spotify for soundtrack")
        
        soundtrack_data = spotify_client.get_soundtrack_with_metadata(title, year)
        
        if soundtrack_data['found']:
            tracks = soundtrack_data['tracks']
            logger.info(f"✓ Found {len(tracks)} tracks from Spotify")
            
            # Convert to standard format
            standardized_tracks = []
            for track in tracks:
                standardized_tracks.append({
                    'title': track['title'],
                    'artist': track['artist'],
                    'composer': '',  # Spotify doesn't provide composer
                    'popularity': track['popularity'],
                    'duration_ms': track['duration_ms'],
                    'audio_features': track.get('audio_features')
                })
            
            # Cache to local database
            if soundtrack_db is not None:
                cache_to_local_db(title, year, imdb_id, standardized_tracks)
            
            return standardized_tracks
    
    return []
```

**Step 3: Configuration**
```python
# In config/secrets.json
{
  "tmdb_api_key": "your_tmdb_key",
  "spotify_client_id": "your_spotify_client_id",
  "spotify_client_secret": "your_spotify_client_secret"
}

# In shared/config.py
class PipelineConfig(BaseSettings):
    use_spotify: bool = Field(default=False, env="USE_SPOTIFY")
    spotify_client_id: str = Field(default="", env="SPOTIFY_CLIENT_ID")
    spotify_client_secret: str = Field(default="", env="SPOTIFY_CLIENT_SECRET")
```

#### Use Cases for Audio Features

**1. Enhanced Lyrics Detection**
```python
# In scripts/lyrics_detection.py

def detect_song_segments(segments, soundtrack_metadata):
    """Use audio features to improve song detection"""
    
    for track in soundtrack_metadata:
        features = track.get('audio_features', {})
        
        # Songs typically have:
        # - Higher danceability (> 0.5)
        # - Higher energy (> 0.6)
        # - Regular tempo
        
        if features.get('danceability', 0) > 0.5:
            # More likely to be a song
            # Apply stricter matching criteria
            pass
```

**2. Song Prioritization**
```python
# Use popularity to prioritize bias terms

def load_song_bias_terms(soundtrack_metadata):
    """Load bias terms, prioritizing popular songs"""
    
    # Sort by popularity
    sorted_tracks = sorted(
        soundtrack_metadata,
        key=lambda x: x.get('popularity', 0),
        reverse=True
    )
    
    # Take top N most popular songs
    return extract_bias_terms(sorted_tracks[:10])
```

#### Pros & Cons

**Pros:**
- ✅ Extremely comprehensive catalog
- ✅ High-quality metadata
- ✅ Audio features for enhanced detection
- ✅ Popularity metrics
- ✅ Easy API integration

**Cons:**
- ❌ Requires API credentials (free tier available)
- ❌ Rate limits (moderate)
- ❌ Doesn't provide composer information
- ❌ Commercial use restrictions
- ❌ Requires internet connection

---

## 3. Automated Soundtrack Scraping

### What It Is
Automated web scraping to extract soundtrack information from public sources like IMDb, Wikipedia, Gaana, JioSaavn, or other music databases.

### Why It's Valuable
- **Comprehensive Coverage**: Can aggregate from multiple sources
- **Free**: No API costs or rate limits
- **Customizable**: Target specific sites with Bollywood content
- **Build Local Database**: Gradually populate local database
- **No External Dependencies**: Once scraped, data is local

### How to Implement

#### Architecture
```
Scraper Service (Background/On-demand)
    ↓
Target: IMDb Soundtracks Page
Target: Wikipedia Movie Infobox
Target: JioSaavn Movie Playlists
    ↓
Parse HTML/JSON for track information
    ↓
Standardize format
    ↓
Add to config/bollywood_soundtracks.json
    ↓
Available for future pipeline runs
```

#### Implementation Steps

**Step 1: IMDb Soundtrack Scraper**
```python
# File: tools/scrape_soundtracks.py

import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import json
from pathlib import Path

class IMDbSoundtrackScraper:
    """Scrape soundtrack information from IMDb"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; SoundtrackScraper/1.0)'
        })
    
    def scrape_soundtrack(self, imdb_id: str) -> Dict:
        """
        Scrape soundtrack from IMDb movie page
        
        Args:
            imdb_id: IMDb identifier (e.g., 'tt0473367')
        
        Returns:
            Soundtrack data dict
        """
        url = f"https://www.imdb.com/title/{imdb_id}/soundtrack"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find soundtrack section
            soundtrack_section = soup.find('div', id='soundtracks_content')
            
            if not soundtrack_section:
                return {'tracks': []}
            
            tracks = []
            # Parse each soundtrack entry
            for item in soundtrack_section.find_all('div', class_='soundTrack'):
                # Extract title
                title_elem = item.find('div', class_='soundTrack-title')
                if not title_elem:
                    continue
                    
                title = title_elem.get_text(strip=True)
                
                # Extract metadata
                metadata = item.find('div', class_='soundTrack-metadata')
                artist = ''
                composer = ''
                
                if metadata:
                    # Look for "Performed by" and "Written by"
                    text = metadata.get_text()
                    
                    if 'Performed by' in text:
                        artist = self._extract_after(text, 'Performed by')
                    elif 'Sung by' in text:
                        artist = self._extract_after(text, 'Sung by')
                    
                    if 'Written by' in text:
                        composer = self._extract_after(text, 'Written by')
                    elif 'Music by' in text:
                        composer = self._extract_after(text, 'Music by')
                
                tracks.append({
                    'title': title,
                    'artist': artist,
                    'composer': composer
                })
            
            return {'tracks': tracks}
            
        except Exception as e:
            print(f"Scraping error for {imdb_id}: {e}")
            return {'tracks': []}
    
    def _extract_after(self, text: str, marker: str) -> str:
        """Extract text after a marker until newline or next marker"""
        start = text.find(marker)
        if start == -1:
            return ''
        
        start += len(marker)
        end = text.find('\n', start)
        if end == -1:
            end = len(text)
        
        return text[start:end].strip()


class WikipediaSoundtrackScraper:
    """Scrape soundtrack from Wikipedia infoboxes"""
    
    def scrape_soundtrack(self, movie_title: str, year: int) -> Dict:
        """
        Scrape soundtrack from Wikipedia movie page
        
        Uses Wikipedia API and parses infobox
        """
        # Search for movie
        search_url = "https://en.wikipedia.org/w/api.php"
        params = {
            'action': 'query',
            'format': 'json',
            'list': 'search',
            'srsearch': f'{movie_title} {year} film soundtrack'
        }
        
        try:
            response = requests.get(search_url, params=params)
            results = response.json()
            
            # Get first result page
            if not results['query']['search']:
                return {'tracks': []}
            
            page_title = results['query']['search'][0]['title']
            
            # Get page content
            content_params = {
                'action': 'parse',
                'format': 'json',
                'page': page_title,
                'prop': 'text'
            }
            
            content_response = requests.get(search_url, params=content_params)
            page_data = content_response.json()
            
            html = page_data['parse']['text']['*']
            soup = BeautifulSoup(html, 'html.parser')
            
            # Look for soundtrack table
            tracks = self._parse_soundtrack_table(soup)
            
            return {'tracks': tracks}
            
        except Exception as e:
            print(f"Wikipedia scraping error: {e}")
            return {'tracks': []}
    
    def _parse_soundtrack_table(self, soup) -> List[Dict]:
        """Parse soundtrack table from Wikipedia page"""
        tracks = []
        
        # Find tables with class 'wikitable' containing soundtrack
        for table in soup.find_all('table', class_='wikitable'):
            header_text = table.find('th')
            if not header_text or 'track' not in header_text.get_text().lower():
                continue
            
            # Parse rows
            for row in table.find_all('tr')[1:]:  # Skip header
                cells = row.find_all('td')
                if len(cells) >= 2:
                    track_data = {
                        'title': cells[1].get_text(strip=True),
                        'artist': cells[2].get_text(strip=True) if len(cells) > 2 else '',
                        'composer': ''
                    }
                    tracks.append(track_data)
        
        return tracks
```

**Step 2: Batch Scraping Script**
```python
# File: tools/build_soundtrack_database.py

#!/usr/bin/env python3
"""
Build soundtrack database by scraping multiple sources
"""

import json
from pathlib import Path
from scrape_soundtracks import IMDbSoundtrackScraper, WikipediaSoundtrackScraper
import time

def build_database_from_movie_list(movie_list_file: str, output_file: str):
    """
    Build soundtrack database from list of movies
    
    Args:
        movie_list_file: JSON file with list of movies [{"title": "...", "year": ..., "imdb_id": "..."}]
        output_file: Output JSON file path
    """
    # Load movie list
    with open(movie_list_file, 'r') as f:
        movies = json.load(f)
    
    # Initialize scrapers
    imdb_scraper = IMDbSoundtrackScraper()
    wiki_scraper = WikipediaSoundtrackScraper()
    
    # Load existing database
    output_path = Path(output_file)
    if output_path.exists():
        with open(output_path, 'r') as f:
            database = json.load(f)
    else:
        database = {}
    
    # Process each movie
    for movie in movies:
        title = movie['title']
        year = movie['year']
        imdb_id = movie.get('imdb_id')
        
        key = f"{title} ({year})"
        
        # Skip if already in database
        if key in database:
            print(f"Skipping {key} - already in database")
            continue
        
        print(f"\nProcessing: {key}")
        
        # Try IMDb first
        soundtrack = None
        if imdb_id:
            print(f"  Scraping IMDb ({imdb_id})...")
            soundtrack = imdb_scraper.scrape_soundtrack(imdb_id)
            time.sleep(2)  # Be respectful
        
        # Try Wikipedia if IMDb failed
        if not soundtrack or not soundtrack['tracks']:
            print(f"  Scraping Wikipedia...")
            soundtrack = wiki_scraper.scrape_soundtrack(title, year)
            time.sleep(2)
        
        # Add to database if found
        if soundtrack and soundtrack['tracks']:
            database[key] = {
                'title': title,
                'year': year,
                'imdb_id': imdb_id,
                'tracks': soundtrack['tracks'],
                'source': 'scraped'
            }
            print(f"  ✓ Found {len(soundtrack['tracks'])} tracks")
            
            # Save after each movie (in case of interruption)
            with open(output_path, 'w') as f:
                json.dump(database, f, indent=2, ensure_ascii=False)
        else:
            print(f"  ✗ No soundtrack found")
    
    print(f"\n✓ Database built with {len(database)} movies")
    print(f"  Saved to: {output_file}")


if __name__ == "__main__":
    # Example: Build from top Bollywood movies list
    build_database_from_movie_list(
        movie_list_file='config/bollywood_movies.json',
        output_file='config/bollywood_soundtracks.json'
    )
```

**Step 3: Movie List for Scraping**
```json
// File: config/bollywood_movies.json
[
  {
    "title": "3 Idiots",
    "year": 2009,
    "imdb_id": "tt1187043"
  },
  {
    "title": "Dangal",
    "year": 2016,
    "imdb_id": "tt5074352"
  },
  {
    "title": "PK",
    "year": 2014,
    "imdb_id": "tt2338151"
  }
  // ... more movies
]
```

**Step 4: Usage**
```bash
# Build soundtrack database
python tools/build_soundtrack_database.py

# Or scrape on-demand during TMDB stage
# If local DB doesn't have data, trigger scraper
```

#### Pros & Cons

**Pros:**
- ✅ Free - no API costs
- ✅ Comprehensive - can scrape multiple sources
- ✅ Builds permanent local database
- ✅ Works offline after scraping
- ✅ Can be run as batch process

**Cons:**
- ❌ Fragile - breaks when websites change
- ❌ Legally gray area (check terms of service)
- ❌ Slower than APIs
- ❌ Requires maintenance
- ❌ May be blocked by rate limiting

---

## 4. Lyrics Alignment

### What It Is
Aligning known song lyrics with the ASR transcript to improve accuracy and timing of song segments. This can also detect when songs are being sung.

### Why It's Valuable
- **Perfect Accuracy**: Known lyrics can replace ASR transcription
- **Timing Correction**: Align ASR timing with actual lyrics
- **Song Detection**: Automatically detect when songs start/end
- **Subtitle Quality**: Ensure lyrics match official versions
- **Multi-version Support**: Handle different renditions

### How to Implement

#### Architecture
```
Stage 7: Song Bias Injection (Enhanced)
    ↓
Load lyrics from database/API
    ↓
Apply sequence alignment algorithm (Smith-Waterman, DTW)
    ↓
Match ASR segments to lyrics
    ↓
Replace low-confidence segments with known lyrics
    ↓
Mark song boundaries
    ↓
Save aligned transcript
```

#### Implementation Steps

**Step 1: Lyrics Database**
```python
# File: scripts/lyrics_database.py

from pathlib import Path
import json
from typing import List, Dict, Optional

class LyricsDatabase:
    """Manage song lyrics database"""
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize lyrics database
        
        Args:
            db_path: Path to lyrics JSON file
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent / "config" / "bollywood_lyrics.json"
        
        self.db_path = db_path
        self.lyrics = self._load_database()
    
    def _load_database(self) -> Dict:
        """Load lyrics from JSON file"""
        if not self.db_path.exists():
            return {}
        
        with open(self.db_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_lyrics(
        self,
        song_title: str,
        movie_title: Optional[str] = None
    ) -> Optional[List[str]]:
        """
        Get lyrics for a song
        
        Args:
            song_title: Song title
            movie_title: Movie title (for disambiguation)
        
        Returns:
            List of lyric lines or None
        """
        # Try exact match
        if movie_title:
            key = f"{movie_title} - {song_title}"
            if key in self.lyrics:
                return self.lyrics[key]['lines']
        
        # Try song title only
        for key, data in self.lyrics.items():
            if song_title.lower() in key.lower():
                return data['lines']
        
        return None
```

**Step 2: Sequence Alignment**
```python
# File: scripts/lyrics_alignment.py

from typing import List, Dict, Tuple
import difflib
from dataclasses import dataclass

@dataclass
class AlignmentResult:
    """Result of lyrics alignment"""
    matched: bool
    start_segment_idx: int
    end_segment_idx: int
    confidence: float
    aligned_lyrics: List[Tuple[str, float, float]]  # (line, start_time, end_time)


class LyricsAligner:
    """Align known lyrics with ASR transcript"""
    
    def __init__(self, similarity_threshold: float = 0.6):
        """
        Initialize aligner
        
        Args:
            similarity_threshold: Minimum similarity to consider a match
        """
        self.similarity_threshold = similarity_threshold
    
    def align_lyrics(
        self,
        lyrics_lines: List[str],
        transcript_segments: List[Dict]
    ) -> AlignmentResult:
        """
        Align lyrics with transcript using sequence matching
        
        Args:
            lyrics_lines: List of lyric lines
            transcript_segments: List of ASR segments
        
        Returns:
            AlignmentResult with matched segments
        """
        # Prepare lyrics and transcript as sequences
        lyrics_text = ' '.join(lyrics_lines).lower()
        lyrics_words = lyrics_text.split()
        
        # Extract words from segments
        segment_words = []
        segment_map = []  # Maps word index to segment index
        for seg_idx, seg in enumerate(transcript_segments):
            words = seg['text'].lower().split()
            segment_words.extend(words)
            segment_map.extend([seg_idx] * len(words))
        
        # Use SequenceMatcher to find best alignment
        matcher = difflib.SequenceMatcher(
            None,
            lyrics_words,
            segment_words
        )
        
        # Find longest matching block
        match = matcher.find_longest_match(
            0, len(lyrics_words),
            0, len(segment_words)
        )
        
        if match.size == 0:
            return AlignmentResult(
                matched=False,
                start_segment_idx=-1,
                end_segment_idx=-1,
                confidence=0.0,
                aligned_lyrics=[]
            )
        
        # Calculate confidence
        confidence = match.size / len(lyrics_words)
        
        if confidence < self.similarity_threshold:
            return AlignmentResult(
                matched=False,
                start_segment_idx=-1,
                end_segment_idx=-1,
                confidence=confidence,
                aligned_lyrics=[]
            )
        
        # Map back to segments
        start_word_idx = match.b
        end_word_idx = match.b + match.size
        
        start_segment_idx = segment_map[start_word_idx]
        end_segment_idx = segment_map[min(end_word_idx, len(segment_map) - 1)]
        
        # Create aligned lyrics with timestamps
        aligned_lyrics = self._create_aligned_lyrics(
            lyrics_lines,
            transcript_segments[start_segment_idx:end_segment_idx + 1]
        )
        
        return AlignmentResult(
            matched=True,
            start_segment_idx=start_segment_idx,
            end_segment_idx=end_segment_idx,
            confidence=confidence,
            aligned_lyrics=aligned_lyrics
        )
    
    def _create_aligned_lyrics(
        self,
        lyrics_lines: List[str],
        matched_segments: List[Dict]
    ) -> List[Tuple[str, float, float]]:
        """
        Create time-aligned lyrics from matched segments
        
        Args:
            lyrics_lines: Original lyric lines
            matched_segments: Matched ASR segments
        
        Returns:
            List of (line, start_time, end_time) tuples
        """
        if not matched_segments:
            return []
        
        # Simple approach: distribute lines evenly across segments
        total_duration = matched_segments[-1]['end'] - matched_segments[0]['start']
        time_per_line = total_duration / len(lyrics_lines)
        
        aligned = []
        current_time = matched_segments[0]['start']
        
        for line in lyrics_lines:
            start = current_time
            end = current_time + time_per_line
            aligned.append((line, start, end))
            current_time = end
        
        return aligned


def replace_with_aligned_lyrics(
    segments: List[Dict],
    alignment: AlignmentResult
) -> List[Dict]:
    """
    Replace ASR segments with aligned lyrics
    
    Args:
        segments: Original ASR segments
        alignment: Alignment result
    
    Returns:
        Updated segments with lyrics
    """
    if not alignment.matched:
        return segments
    
    # Create new segments for lyrics
    lyric_segments = []
    for line, start, end in alignment.aligned_lyrics:
        lyric_segments.append({
            'text': line,
            'start': start,
            'end': end,
            'is_lyrics': True,
            'confidence': alignment.confidence
        })
    
    # Replace matched segments
    new_segments = (
        segments[:alignment.start_segment_idx] +
        lyric_segments +
        segments[alignment.end_segment_idx + 1:]
    )
    
    return new_segments
```

**Step 3: Integration**
```python
# File: scripts/song_bias_injection.py (enhanced)

from scripts.lyrics_database import LyricsDatabase
from scripts.lyrics_alignment import LyricsAligner, replace_with_aligned_lyrics

def main():
    # ... existing code ...
    
    # Load lyrics database
    lyrics_db = LyricsDatabase()
    aligner = LyricsAligner(similarity_threshold=0.65)
    
    # For each song in soundtrack
    for song in soundtrack_tracks:
        song_title = song['title']
        
        # Get lyrics
        lyrics = lyrics_db.get_lyrics(song_title, movie_title)
        
        if lyrics:
            logger.info(f"Attempting to align lyrics for: {song_title}")
            
            # Align with transcript
            alignment = aligner.align_lyrics(lyrics, segments)
            
            if alignment.matched:
                logger.info(f"✓ Aligned lyrics (confidence: {alignment.confidence:.2f})")
                logger.info(f"  Segments {alignment.start_segment_idx} to {alignment.end_segment_idx}")
                
                # Replace segments with aligned lyrics
                segments = replace_with_aligned_lyrics(segments, alignment)
            else:
                logger.info(f"✗ Could not align lyrics (confidence: {alignment.confidence:.2f})")
    
    # ... save segments ...
```

**Step 4: Lyrics Database Format**
```json
// File: config/bollywood_lyrics.json
{
  "Jaane Tu... Ya Jaane Na - Kabhi Kabhi Aditi": {
    "movie": "Jaane Tu... Ya Jaane Na",
    "song": "Kabhi Kabhi Aditi",
    "language": "Hindi",
    "lines": [
      "Kabhi kabhi Aditi, zindagi mein yun hi",
      "Koi apna lagta hai, koi aur lagta hai",
      "Kabhi kabhi Aditi, woh bichad jaate hain",
      "Jo kareeb lagta hai, kaash aisa na ho"
    ],
    "source": "official_lyrics"
  }
}
```

#### Advanced: Dynamic Time Warping

For more accurate alignment:

```python
# File: scripts/dtw_alignment.py

import numpy as np
from scipy.spatial.distance import cosine

def dtw_align(
    lyrics_embedding: np.ndarray,
    transcript_embedding: np.ndarray
) -> np.ndarray:
    """
    Align lyrics using Dynamic Time Warping
    
    Args:
        lyrics_embedding: Embeddings for lyric words
        transcript_embedding: Embeddings for transcript words
    
    Returns:
        Alignment path
    """
    n, m = len(lyrics_embedding), len(transcript_embedding)
    
    # Initialize cost matrix
    cost = np.full((n + 1, m + 1), np.inf)
    cost[0, 0] = 0
    
    # Calculate DTW
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            distance = cosine(lyrics_embedding[i-1], transcript_embedding[j-1])
            cost[i, j] = distance + min(
                cost[i-1, j],    # Insertion
                cost[i, j-1],    # Deletion
                cost[i-1, j-1]   # Match
            )
    
    # Backtrack to find path
    path = []
    i, j = n, m
    while i > 0 and j > 0:
        path.append((i-1, j-1))
        
        # Choose minimum cost direction
        costs = [cost[i-1, j-1], cost[i-1, j], cost[i, j-1]]
        direction = np.argmin(costs)
        
        if direction == 0:
            i, j = i-1, j-1
        elif direction == 1:
            i = i-1
        else:
            j = j-1
    
    return np.array(list(reversed(path)))
```

#### Pros & Cons

**Pros:**
- ✅ Perfect lyric accuracy
- ✅ Improved timing
- ✅ Automatic song detection
- ✅ Better subtitle quality
- ✅ Handles ASR errors

**Cons:**
- ❌ Requires lyrics database
- ❌ Complex alignment algorithms
- ❌ May fail on variations
- ❌ Computationally intensive
- ❌ Doesn't work for unreleased songs

---

## 5. Multi-language Support

### What It Is
Support for soundtracks with songs in multiple languages (Hindi, Punjabi, Tamil, Telugu, English) within the same movie.

### Why It's Valuable
- **Bollywood Reality**: Many movies have multi-language songs
- **Regional Films**: South Indian films often have Tamil/Telugu versions
- **Correct Language Detection**: Apply proper bias terms per language
- **Better Accuracy**: Language-specific models for each segment
- **Subtitle Quality**: Proper character sets and formatting

### How to Implement

#### Architecture
```
Song Bias Injection (Enhanced)
    ↓
Detect language of each track from metadata
    ↓
Apply language-specific bias terms
    ↓
Tag segments with detected language
    ↓
Lyrics Detection uses language info
    ↓
Subtitle Gen applies language-specific formatting
```

#### Implementation Steps

**Step 1: Multi-language Soundtrack Database**
```json
// File: config/bollywood_soundtracks.json (enhanced)
{
  "RRR (2022)": {
    "title": "RRR",
    "year": 2022,
    "imdb_id": "tt8178634",
    "tracks": [
      {
        "title": "Naatu Naatu",
        "artist": "Rahul Sipligunj, Kaala Bhairava",
        "composer": "M. M. Keeravani",
        "language": "Telugu",
        "translations": {
          "Hindi": "Nacho Nacho",
          "Tamil": "Naatu Koothu"
        }
      },
      {
        "title": "Dosti",
        "artist": "Arijit Singh",
        "composer": "M. M. Keeravani",
        "language": "Hindi"
      },
      {
        "title": "Etthara Jenda",
        "artist": "Vishal Mishra",
        "composer": "M. M. Keeravani",
        "language": "Telugu",
        "transliteration": {
          "Hindi": "इत्थरा जेंडा",
          "English": "Etthara Jenda"
        }
      }
    ]
  }
}
```

**Step 2: Language Detection**
```python
# File: scripts/language_detector.py

from typing import Dict, List, Optional
import langdetect
from collections import Counter

class LanguageDetector:
    """Detect language of text segments"""
    
    # Language code mapping
    LANGUAGE_MAP = {
        'hi': 'Hindi',
        'en': 'English',
        'te': 'Telugu',
        'ta': 'Tamil',
        'pa': 'Punjabi',
        'bn': 'Bengali',
        'ml': 'Malayalam',
        'kn': 'Kannada'
    }
    
    def detect_segment_language(
        self,
        text: str,
        fallback: str = 'Hindi'
    ) -> str:
        """
        Detect language of a text segment
        
        Args:
            text: Text to analyze
            fallback: Default language if detection fails
        
        Returns:
            Language name
        """
        if not text or len(text) < 3:
            return fallback
        
        try:
            code = langdetect.detect(text)
            return self.LANGUAGE_MAP.get(code, fallback)
        except:
            return fallback
    
    def detect_predominant_language(
        self,
        segments: List[Dict],
        window_size: int = 5
    ) -> List[str]:
        """
        Detect language for each segment using context window
        
        Args:
            segments: List of transcript segments
            window_size: Number of segments to consider for context
        
        Returns:
            List of language names (one per segment)
        """
        languages = []
        
        for i, seg in enumerate(segments):
            # Get context window
            start = max(0, i - window_size // 2)
            end = min(len(segments), i + window_size // 2 + 1)
            
            window_segments = segments[start:end]
            window_text = ' '.join([s['text'] for s in window_segments])
            
            # Detect language
            lang = self.detect_segment_language(window_text)
            languages.append(lang)
        
        return languages
    
    def get_language_distribution(
        self,
        segments: List[Dict],
        languages: List[str]
    ) -> Dict[str, float]:
        """
        Get distribution of languages in transcript
        
        Args:
            segments: Transcript segments
            languages: Language per segment
        
        Returns:
            Dict of language percentages
        """
        total_duration = sum(seg['end'] - seg['start'] for seg in segments)
        
        language_durations = {}
        for seg, lang in zip(segments, languages):
            duration = seg['end'] - seg['start']
            language_durations[lang] = language_durations.get(lang, 0) + duration
        
        return {
            lang: (dur / total_duration) * 100
            for lang, dur in language_durations.items()
        }
```

**Step 3: Language-specific Bias Terms**
```python
# File: scripts/song_bias_injection.py (enhanced)

from scripts.language_detector import LanguageDetector

def load_song_bias_terms_multilingual(
    stage_io: StageIO,
    logger: PipelineLogger
) -> Dict[str, List[str]]:
    """
    Load song bias terms organized by language
    
    Returns:
        Dict mapping language to bias terms
    """
    # Load soundtrack
    tmdb_file = stage_io.output_base / "02_tmdb" / "enrichment.json"
    with open(tmdb_file, 'r', encoding='utf-8') as f:
        tmdb_data = json.load(f)
    
    soundtrack = tmdb_data.get('soundtrack', [])
    
    # Organize by language
    bias_by_language = {}
    
    for song in soundtrack:
        lang = song.get('language', 'Hindi')
        
        if lang not in bias_by_language:
            bias_by_language[lang] = []
        
        # Add song title
        title = song.get('title', '').strip()
        if title:
            bias_by_language[lang].append(title)
        
        # Add artist names
        artist = song.get('artist', '').strip()
        if artist:
            for name in artist.split(','):
                name = name.strip()
                if name:
                    bias_by_language[lang].append(name)
        
        # Add composer
        composer = song.get('composer', '').strip()
        if composer:
            bias_by_language[lang].append(composer)
        
        # Add translations
        translations = song.get('translations', {})
        for trans_lang, trans_title in translations.items():
            if trans_lang not in bias_by_language:
                bias_by_language[trans_lang] = []
            bias_by_language[trans_lang].append(trans_title)
    
    # Log summary
    for lang, terms in bias_by_language.items():
        logger.info(f"  {lang}: {len(terms)} bias terms")
    
    return bias_by_language


def main():
    # ... load segments ...
    
    # Detect language per segment
    detector = LanguageDetector()
    segment_languages = detector.detect_predominant_language(segments)
    
    # Get language distribution
    lang_dist = detector.get_language_distribution(segments, segment_languages)
    logger.info("Language distribution:")
    for lang, pct in lang_dist.items():
        logger.info(f"  {lang}: {pct:.1f}%")
    
    # Load language-specific bias terms
    bias_by_language = load_song_bias_terms_multilingual(stage_io, logger)
    
    # Apply corrections per language
    corrected_segments = []
    for seg, lang in zip(segments, segment_languages):
        bias_terms = bias_by_language.get(lang, [])
        
        if bias_terms:
            # Create language-specific corrector
            corrector = BiasCorrector(
                bias_terms=bias_terms,
                fuzzy_threshold=0.80,
                logger=logger
            )
            
            corrected_seg, stats = corrector.correct_segments([seg])
            corrected_seg[0]['detected_language'] = lang
            corrected_segments.extend(corrected_seg)
        else:
            seg['detected_language'] = lang
            corrected_segments.append(seg)
    
    # ... save segments ...
```

**Step 4: Language-specific Subtitle Formatting**
```python
# File: scripts/subtitle_gen.py (enhanced)

def format_subtitle_for_language(
    text: str,
    language: str
) -> str:
    """
    Apply language-specific formatting
    
    Args:
        text: Subtitle text
        language: Detected language
    
    Returns:
        Formatted text
    """
    # Apply language-specific rules
    if language == 'Hindi':
        # Optional: Add Devanagari script
        # text = transliterate_to_devanagari(text)
        pass
    elif language == 'Tamil':
        # Tamil-specific formatting
        pass
    elif language == 'Telugu':
        # Telugu-specific formatting
        pass
    
    return text


def generate_srt_multilingual(
    segments: List[Dict],
    output_path: Path
):
    """Generate SRT with language tags"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, seg in enumerate(segments, 1):
            # Format timestamp
            start = format_timestamp(seg['start'])
            end = format_timestamp(seg['end'])
            
            # Get language and format text
            lang = seg.get('detected_language', 'Hindi')
            text = format_subtitle_for_language(seg['text'], lang)
            
            # Add language tag as comment (optional)
            # f.write(f"<!-- Language: {lang} -->\n")
            
            # Write subtitle entry
            f.write(f"{i}\n")
            f.write(f"{start} --> {end}\n")
            f.write(f"{text}\n\n")
```

#### Pros & Cons

**Pros:**
- ✅ Accurate for multilingual content
- ✅ Better bias term application
- ✅ Language-aware processing
- ✅ Handles regional variations
- ✅ Improved subtitle quality

**Cons:**
- ❌ More complex metadata management
- ❌ Language detection not 100% accurate
- ❌ Requires language-specific models
- ❌ More processing time
- ❌ Harder to maintain database

---

## Implementation Priority

### Recommended Order

1. **MusicBrainz API** (High Priority)
   - Most impactful
   - Free and reliable
   - Good data quality
   - Relatively easy to implement

2. **Automated Scraping** (Medium Priority)
   - Fills gaps in MusicBrainz
   - Good for building local database
   - One-time setup effort

3. **Multi-language Support** (Medium Priority)
   - Important for accuracy
   - Moderate complexity
   - High value for regional films

4. **Lyrics Alignment** (Low Priority)
   - Most complex
   - Requires lyrics database
   - High accuracy benefit but limited use cases

5. **Spotify API** (Optional)
   - Nice-to-have
   - Requires credentials
   - Good for audio features

### Quick Win: Start with MusicBrainz

```bash
# Install dependency
pip install musicbrainzngs

# Add to tmdb_enrichment.py
# Test with existing movie
python scripts/tmdb.py
```

---

## Summary

Each enhancement addresses specific needs:
- **MusicBrainz**: Automated data fetching
- **Spotify**: Rich metadata + audio features
- **Scraping**: Build comprehensive local database
- **Lyrics Alignment**: Perfect accuracy for songs
- **Multi-language**: Handle Bollywood's linguistic diversity

All enhancements are **technically feasible** and would integrate into the existing architecture without major refactoring.
