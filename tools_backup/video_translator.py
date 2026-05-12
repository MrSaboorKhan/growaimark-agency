"""
AI Video Translator Tool - Using Google Gemini API
Supports YouTube, Instagram, Facebook, TikTok videos
"""

import os
import re
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from yt_dlp import YoutubeDL
import google.generativeai as genai
from urllib.parse import urlparse, parse_qs

# Configure Gemini API
# API key ko environment variable mein rakhna better hai
GEMINI_API_KEY = os.environ.get('AIzaSyBp3Yd9wa1Kwz1trRwA7USBDOupbpK9sq4', 'c913b01d36574e3eaf19ee987e6ab54c607527ec84750b2913f59e637bda3ca2')
genai.configure(api_key=GEMINI_API_KEY)

# Translation cache (taake same content baar baar na translate ho)
translation_cache = {}


class VideoTranslator:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def extract_video_id(self, url):
        """Extract video ID from various platform URLs"""
        # YouTube
        if 'youtube.com' in url or 'youtu.be' in url:
            if 'youtu.be' in url:
                return url.split('/')[-1].split('?')[0]
            parsed = urlparse(url)
            return parse_qs(parsed.query).get('v', [None])[0]
        # Instagram Reel
        elif 'instagram.com' in url:
            # Extract reel ID from URL
            match = re.search(r'/reel/([^/?]+)', url)
            return match.group(1) if match else None
        return None

    def get_youtube_transcript(self, video_id):
        """Get transcript from YouTube video"""
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            # Try to get English transcript first
            try:
                transcript = transcript_list.find_transcript(['en'])
            except:
                # If no English, get any available and translate to English
                transcript = transcript_list.find_transcript(['ur', 'hi', 'en'])

            transcript_data = transcript.fetch()
            full_text = ' '.join([entry['text'] for entry in transcript_data])
            return full_text
        except Exception as e:
            return None

    def download_instagram_audio(self, url):
        """Download audio from Instagram reel using yt-dlp"""
        try:
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': 'temp_audio.%(ext)s',
                'quiet': True,
                'no_warnings': True,
            }
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return 'temp_audio.webm'  # or appropriate extension
        except Exception as e:
            return None

    def transcribe_audio_with_gemini(self, audio_path):
        """Transcribe audio using Gemini's multimodal capabilities"""
        try:
            # Gemini 2.0 supports audio input [citation:2]
            import base64
            with open(audio_path, 'rb') as f:
                audio_data = base64.b64encode(f.read()).decode()

            prompt = """Transcribe the following audio accurately.
            Output only the transcribed text, no extra explanations.
            If there are multiple speakers, indicate them."""

            response = self.model.generate_content([
                prompt,
                {"mime_type": "audio/webm", "data": audio_data}
            ])
            return response.text
        except Exception as e:
            return f"Transcription error: {str(e)}"

    def translate_text(self, text, target_language='urdu'):
        """Translate text using Gemini API with natural, easy-to-understand output"""

        # Check cache first
        cache_key = f"{hash(text)}_{target_language}"
        if cache_key in translation_cache:
            return translation_cache[cache_key]

        # Smart prompting for natural translation
        prompt = f"""You are a professional translator. Translate the following text to {target_language}.

CRITICAL RULES:
1. Use NATURAL, conversational language that a native speaker would use
2. Make it EASY TO UNDERSTAND - avoid complex vocabulary
3. Keep the original meaning and tone (formal/informal/casual/serious)
4. Adapt idioms and cultural references appropriately
5. Do NOT add any explanations, notes, or extra text
6. Output ONLY the translation, nothing else

Text to translate:
{text}

Translation to {target_language}:"""

        try:
            response = self.model.generate_content(prompt)
            translated = response.text.strip()

            # Cache the result
            translation_cache[cache_key] = translated
            return translated
        except Exception as e:
            return f"Translation error: {str(e)}"

    def translate_batch(self, texts, target_language='urdu'):
        """Translate multiple texts in one API call (more efficient)"""
        prompt = f"""You are a professional translator. Translate the following texts to {target_language}.

RULES:
- Translate each text naturally and conversationally
- Make it SIMPLE and EASY TO UNDERSTAND
- Output as a JSON array, keeping the exact same order
- Do NOT add any extra text or explanations

Texts to translate:
{texts}

Output format: ["translation1", "translation2", ...]"""

        try:
            response = self.model.generate_content(prompt)
            import json
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
            if json_match:
                translations = json.loads(json_match.group())
                return translations
            return [response.text]
        except Exception as e:
            return [f"Error: {str(e)}"]

    def process_video(self, url, target_language='urdu'):
        """Main function to process video and return translation"""
        result = {
            'success': False,
            'original_text': '',
            'translated_text': '',
            'language': target_language,
            'video_id': None,
            'platform': 'unknown'
        }

        # Identify platform
        if 'youtube.com' in url or 'youtu.be' in url:
            result['platform'] = 'youtube'
            video_id = self.extract_video_id(url)
            result['video_id'] = video_id

            # Get transcript
            original_text = self.get_youtube_transcript(video_id)
            if original_text:
                result['original_text'] = original_text[:3000]  # Limit length
                # Translate
                translated = self.translate_text(original_text[:3000], target_language)
                result['translated_text'] = translated
                result['success'] = True

        elif 'instagram.com' in url:
            result['platform'] = 'instagram'
            result['video_id'] = self.extract_video_id(url)
            # For Instagram, we'd need audio transcription
            # This is a placeholder for now
            result['original_text'] = "Instagram Reel detected. Audio transcription coming soon!"
            result['translated_text'] = await self.translate_text(result['original_text'], target_language)
            result['success'] = True

        return result

    def translate_direct_text(self, text, target_language='urdu'):
        """Direct text translation without video processing"""
        if not text or len(text.strip()) == 0:
            return {'success': False, 'error': 'No text provided'}

        translated = self.translate_text(text, target_language)
        return {
            'success': True,
            'original': text,
            'translated': translated,
            'language': target_language
        }


# Test the tool
if __name__ == "__main__":
    translator = VideoTranslator()

    # Test with a YouTube video
    test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    result = translator.process_video(test_url, 'urdu')
    print(f"Result: {result}")