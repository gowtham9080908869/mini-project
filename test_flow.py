import urllib.request
import urllib.parse
import json
import http.cookiejar

base_url = 'http://localhost:5000'
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

def get(url):
    try:
        with opener.open(url) as response:
            return response.status, response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')

def post(url, data):
    try:
        json_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=json_data, headers={'Content-Type': 'application/json'})
        with opener.open(req) as response:
            return response.status, response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')

# 1. Start verification
print("1. Starting verification...")
status, text = get(f'{base_url}/start_verification')
print(status, text[:100])

# 2. Fail Text CAPTCHA twice
print("\n2. Failing Text CAPTCHA (attempt 1)...")
status, text = post(f'{base_url}/verify_captcha', {'answer': 'wrong'})
print(status, text)

print("   Failing Text CAPTCHA (attempt 2)...")
status, text = post(f'{base_url}/verify_captcha', {'answer': 'wrong'})
print(status, text)

# 3. Get Image Challenge (should trigger generate_challenge_images)
print("\n3. Getting Image Challenge...")
status, text = get(f'{base_url}/get_current_challenge')
print(status, text)

# 4. Fail Image CAPTCHA twice
print("\n4. Failing Image CAPTCHA (attempt 1)...")
status, text = post(f'{base_url}/verify_captcha', {'selected': []}) # Empty selection should be wrong
print(status, text)

print("   Failing Image CAPTCHA (attempt 2)...")
status, text = post(f'{base_url}/verify_captcha', {'selected': []})
print(status, text)

# 5. Get Part Selection Challenge
print("\n5. Getting Part Challenge...")
status, text = get(f'{base_url}/get_current_challenge')
print(status, text)
