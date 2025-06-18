from fastapi import FastAPI, HTTPException
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled, 
    NoTranscriptFound, 
    VideoUnavailable,
    RequestBlocked,
    YouTubeRequestFailed
)
import uvicorn
from typing import List, Dict, Any
from pydantic import BaseModel

class VideoRequest(BaseModel):
    id: str

class TranscriptSegment(BaseModel):
    text: str
    duration: str
    offset: str
    lang: str

class BatchResponseItem(BaseModel):
    success: bool
    transcript: List[TranscriptSegment] = None
    error: str = None

app = FastAPI(
    title="YouTube Transcript API",
    description="A FastAPI server that fetches transcript data for YouTube videos",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "YouTube Transcript API Server",
        "docs": "/docs",
        "health": "/health"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.get("/transcript/{video_id}")
async def get_transcript(video_id: str) -> List[Dict[str, Any]]:
    """
    Fetch transcript data for a YouTube video.
    
    Args:
        video_id (str): The YouTube video ID (not the full URL)
        
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
    try:
        # Initialize the YouTube Transcript API
        ytt_api = YouTubeTranscriptApi()
        
        # Fetch the transcript
        fetched_transcript = ytt_api.fetch(video_id)
        
        # Convert to raw data format
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
async def get_available_languages(video_id: str):
    """
    Get available transcript languages for a YouTube video.
    
    Args:
        video_id (str): The YouTube video ID
        
    Returns:
        List of available transcript languages and metadata
    """
    try:
        ytt_api = YouTubeTranscriptApi()
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
async def get_batch_transcript(video_requests: List[VideoRequest]) -> List[BatchResponseItem]:
    """
    Fetch transcripts for a batch of YouTube videos.
    
    Args:
        video_requests (List[VideoRequest]): List of video requests with IDs
        
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
    
    for video_request in video_requests:
        video_id = video_request.id
        try:
            # Initialize the YouTube Transcript API
            ytt_api = YouTubeTranscriptApi()
            
            # Fetch the transcript
            fetched_transcript = ytt_api.fetch(video_id)
            
            # Convert to the requested format
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
