import os
import requests
import json

def fetch_useful_links(state):
    destination = state['preferences'].get('destination', '')
    month = state['preferences'].get('month', '')
    query = f"Travel tips and guides for {destination} in {month}"
    
    # Check if API key is available
    api_key = os.environ.get('PERPLEXITY_API_KEY')
    if not api_key:
        print("PERPLEXITY_API_KEY not found in environment variables")
        return {"useful_links": [
            {"title": f"Travel Guide for {destination}", "link": f"https://www.google.com/search?q=travel+guide+{destination}+{month}"},
            {"title": f"{destination} Tourism", "link": f"https://www.google.com/search?q={destination}+tourism+{month}"},
            {"title": f"Best Time to Visit {destination}", "link": f"https://www.google.com/search?q=best+time+visit+{destination}"}
        ], "warning": "PERPLEXITY_API_KEY not set. Please add it to your .env file."}
    
    try:
        url = "https://api.perplexity.ai/chat/completions"
        
        payload = {
            "model": "sonar",
            "messages": [
                {"role": "system", "content": "You are a travel assistant. Search for and return exactly 5 useful travel links for the given destination and month. Return ONLY a JSON object with this exact format: {\"links\": [{\"title\": \"Title here\", \"link\": \"URL here\"}, ...]}"},
                {"role": "user", "content": query}
            ]
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        print(f"Making request to Perplexity API with key: {api_key[:10]}...")  # Debug print
        
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(f"Perplexity response: {content}")  # Debug print
            
            # Try to parse the JSON response
            try:
                # Clean the response content - remove markdown code blocks if present
                content = content.strip()
                if content.startswith('```json'):
                    content = content[7:]  # Remove ```json
                if content.endswith('```'):
                    content = content[:-3]  # Remove ```
                content = content.strip()
                
                data = json.loads(content)
                links = data.get("links", [])
                
                # Validate links format
                valid_links = []
                for link in links[:5]:  # Take first 5
                    if isinstance(link, dict) and "title" in link and "link" in link:
                        valid_links.append({
                            "title": link["title"],
                            "link": link["link"]
                        })
                
                if valid_links:
                    return {"useful_links": valid_links}
                else:
                    # Fallback: create a simple response
                    return {"useful_links": [
                        {"title": f"Travel Guide for {destination}", "link": f"https://www.google.com/search?q=travel+guide+{destination}+{month}"},
                        {"title": f"{destination} Tourism", "link": f"https://www.google.com/search?q={destination}+tourism+{month}"},
                        {"title": f"Best Time to Visit {destination}", "link": f"https://www.google.com/search?q=best+time+visit+{destination}"}
                    ]}
                    
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {e}")
                # Fallback response
                return {"useful_links": [
                    {"title": f"Travel Guide for {destination}", "link": f"https://www.google.com/search?q=travel+guide+{destination}+{month}"},
                    {"title": f"{destination} Tourism", "link": f"https://www.google.com/search?q={destination}+tourism+{month}"}
                ]}
        else:
            print(f"API error: {response.status_code} - {response.text}")
            # Fallback response on API error
            return {"useful_links": [
                {"title": f"Travel Guide for {destination}", "link": f"https://www.google.com/search?q=travel+guide+{destination}+{month}"},
                {"title": f"{destination} Tourism", "link": f"https://www.google.com/search?q={destination}+tourism+{month}"}
            ], "warning": f"API error {response.status_code}: {response.text}"}
            
    except Exception as e:
        print(f"Request error: {e}")
        # Fallback response on any error
        return {"useful_links": [
            {"title": f"Travel Guide for {destination}", "link": f"https://www.google.com/search?q=travel+guide+{destination}+{month}"},
            {"title": f"{destination} Tourism", "link": f"https://www.google.com/search?q={destination}+tourism+{month}"}
        ], "warning": f"Using fallback links due to error: {str(e)}"}