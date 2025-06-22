from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled, 
    NoTranscriptFound, 
    VideoUnavailable,
    RequestBlocked,
    YouTubeRequestFailed
)
from youtube_transcript_api.proxies import WebshareProxyConfig
import uvicorn
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from typing import Annotated
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Environment variables
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5678").split(",")
PROXY_USERNAME= os.getenv("PROXY_USERNAME", "")
PROXY_PASSWORD = os.getenv("PROXY_PASSWORD", "")

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

if not DEBUG:
    ytt_api = YouTubeTranscriptApi(
        proxy_config=WebshareProxyConfig(
            proxy_username=PROXY_USERNAME,
            proxy_password=PROXY_PASSWORD,
        )
    )
else:
    ytt_api = YouTubeTranscriptApi()


class VideoRequest(BaseModel):
    # YouTube video IDs are exactly 11 characters, alphanumeric with hyphens and underscores
    id: Annotated[str, Field(min_length=11, max_length=11, pattern=r"^[A-Za-z0-9_-]{11}$")]
    
    @field_validator('id')
    @classmethod
    def validate_video_id(cls, v):
        # Additional validation for YouTube video ID format
        if not v or len(v) != 11:
            raise ValueError('Video ID must be exactly 11 characters')
        return v

class TranscriptSegment(BaseModel):
    text: str
    duration: str
    offset: str
    lang: str

class BatchResponseItem(BaseModel):
    success: bool
    transcript: Optional[List[TranscriptSegment]] = None
    error: Optional[str] = None

app = FastAPI(
    title="YouTube Transcript API",
    description="A FastAPI server that fetches transcript data for YouTube videos",
    version="1.0.0",
    redirect_slashes=False
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Trusted hosts
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=ALLOWED_HOSTS + ["transcript." + host for host in ALLOWED_HOSTS if not host.startswith("localhost")]
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    max_age=3600,
)

@app.get("/")
@limiter.limit("30/minute")
async def root(request: Request):
    """Root endpoint with API information"""
    return {
        "message": "YouTube Transcript API Server",
        "docs": "/docs",
        "health": "/health",
        "version": "1.0.0"
    }

@app.get("/health")
@limiter.limit("60/minute")
async def health_check(request: Request):
    """Health check endpoint"""
    return {"status": "healthy", "service": "youtube-transcript-api"}

@app.get("/transcript/{video_id}")
@limiter.limit("100/minute")
async def get_transcript(video_id: str, request: Request) -> List[Dict[str, Any]]:
    """
    Fetch transcript data for a YouTube video.
    
    Args:
        video_id (str): The YouTube video ID (not the full URL) - must be exactly 11 characters
        
    Returns:
        List[Dict[str, Any]]: Raw transcript data with text, start time, and duration
        
    Example:
        GET /transcript/dQw4w9WgXcQ
        
        Returns:
        [
            {
                "text": "Hey there",
                "start": 0.0,
                "duration": 1.54
            },
            {
                "text": "how are you",
                "start": 1.54,
                "duration": 4.16
            }
        ]
    """
    # Validate video ID format
    if not video_id or len(video_id) != 11:
        raise HTTPException(
            status_code=400, 
            detail="Invalid video ID format. YouTube video IDs must be exactly 11 characters."
        )
    
    try:
        print(f"Fetching transcript for video ID: {video_id}")

        fetched_transcript = ytt_api.fetch(video_id)
        raw_transcript_data = fetched_transcript.to_raw_data()
        
        return raw_transcript_data
        
    except VideoUnavailable:
        raise HTTPException(
            status_code=404, 
            detail=f"Video with ID '{video_id}' is not available"
        )
    except NoTranscriptFound:
        raise HTTPException(
            status_code=404, 
            detail=f"No transcript found for video ID '{video_id}'"
        )
    except TranscriptsDisabled:
        raise HTTPException(
            status_code=403, 
            detail=f"Transcripts are disabled for video ID '{video_id}'"
        )
    except RequestBlocked:
        raise HTTPException(
            status_code=429, 
            detail="Request blocked. Please try again later."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while fetching the transcript: {str(e)}"
        )

@app.get("/transcript/{video_id}/languages")
@limiter.limit("60/minute")
async def get_available_languages(video_id: str, request: Request):
    """
    Get available transcript languages for a YouTube video.
    
    Args:
        video_id (str): The YouTube video ID - must be exactly 11 characters
        
    Returns:
        List of available transcript languages and metadata
    """
    # Validate video ID format
    if not video_id or len(video_id) != 11:
        raise HTTPException(
            status_code=400, 
            detail="Invalid video ID format. YouTube video IDs must be exactly 11 characters."
        )
    
    try:
        print(f"Fetching transcript languages for video ID: {video_id}")

        transcript_list = ytt_api.list(video_id)
        available_transcripts = []

        for transcript in transcript_list:
            available_transcripts.append({
                "language": transcript.language,
                "language_code": transcript.language_code,
                "is_generated": transcript.is_generated,
                "is_translatable": transcript.is_translatable,
            })
            
        return {
            "video_id": video_id,
            "available_transcripts": available_transcripts
        }
        
    except VideoUnavailable:
        raise HTTPException(
            status_code=404, 
            detail=f"Video with ID '{video_id}' is not available"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"An error occurred while fetching transcript list: {str(e)}"
        )

@app.post("/transcript/batch")
@limiter.limit("20/minute")
async def get_batch_transcript(
    video_requests: Annotated[List[VideoRequest], Field(min_length=1, max_length=10)],
    request: Request
) -> List[BatchResponseItem]:
    """
    Fetch transcripts for a batch of YouTube videos.
    
    Args:
        video_requests (List[VideoRequest]): List of video requests with IDs (max 10 videos)
        
    Returns:
        List[BatchResponseItem]: List of transcript results with success status
        
    Example request:
        [
            {"id": "eK_KWWxU6gY"},
            {"id": "BDD_Ppcnpfs"}
        ]
        
    Example response:
        [
            {
                "success": true,
                "transcript": [
                    {
                        "text": "Today we're going to be looking at",
                        "duration": "4.40",
                        "offset": "0.24", 
                        "lang": "en"
                    }
                ]
            }
        ]
    """
    responses = []

    print(f"Received batch request for {len(video_requests)} videos")
    
    for video_request in video_requests:
    
        video_id = video_request.id

        try:
            fetched_transcript = ytt_api.fetch(video_id)
            transcript_segments = []

            for segment in fetched_transcript:
                transcript_segments.append({
                    "text": segment.text,
                    "duration": str(segment.duration),
                    "offset": str(segment.start),
                    "lang": fetched_transcript.language_code
                })
            
            responses.append({
                "success": True,
                "transcript": transcript_segments
            })
            
        except VideoUnavailable:
            responses.append({
                "success": False,
                "error": f"Video with ID '{video_id}' is not available"
            })
        except NoTranscriptFound:
            responses.append({
                "success": False,
                "error": f"No transcript found for video ID '{video_id}'"
            })
        except TranscriptsDisabled:
            responses.append({
                "success": False,
                "error": f"Transcripts are disabled for video ID '{video_id}'"
            })
        except RequestBlocked:
            responses.append({
                "success": False,
                "error": "Request blocked. Please try again later."
            })
        except Exception as e:
            responses.append({
                "success": False,
                "error": f"An error occurred while fetching the transcript: {str(e)}"
            })
    
    return responses

if __name__ == "__main__":
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=int(os.getenv("PORT", "8000")),
        log_level="info" if not DEBUG else "debug"
    )
