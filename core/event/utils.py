import os
import mimetypes
import numpy as np
import google.generativeai as genai

genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))

def parse_embedding_response(response):
    """
    Extract embedding vector from Google's embedding response.
    Always returns a list of floats or None.
    """
    try:
        if isinstance(response, dict) and "embedding" in response:
            return response["embedding"]

        # If response is an object (sometimes SDK returns structured object)
        if hasattr(response, "embedding"):
            return response.embedding

        print("❌ Unexpected embedding response format:", response)
        return None
    except Exception as e:
        print("❌ parse_embedding_response error:", str(e))
        return None


def get_image_embedding(image_path):
    """
    Generate an embedding vector for an image by first describing it with Gemini,
    then embedding the description text.
    """
    try:
        print("📂 Entering get_image_embedding with:", image_path)

        mime_type, _ = mimetypes.guess_type(image_path)
        if not mime_type:
            mime_type = "image/jpeg"

        with open(image_path, "rb") as f:
            image_bytes = f.read()

        image_parts = [{"mime_type": mime_type, "data": image_bytes}]

        # Step 1: Describe image
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(["Describe this image in detail.", *image_parts])
        description = (getattr(response, "text", "") or "").strip()

        print("📝 Gemini Description:", description if description else "[EMPTY]")
        if not description:
            return None

        # Step 2: Embed the description
        embedding_response = genai.embed_content(
            model="models/text-embedding-004",  # ✅ latest embedding model
            content=description
        )

        embedding = parse_embedding_response(embedding_response)
        if not embedding:
            print("❌ Could not extract embedding")
            return None

        # Validate
        arr = np.array(embedding, dtype=np.float32)
        if arr.size == 0 or np.any(np.isnan(arr)):
            print("❌ Invalid embedding")
            return None

        print(f"📊 Extracted embedding length: {len(arr)}")
        return arr.tolist()

    except Exception as e:
        print("❌ Error generating embedding:", str(e))
        return None
