import requests

url = "http://localhost:8000/api/candidates/upload"
files = {'files': ('resume.pdf', b'Python React AWS node.js sql html css', 'application/pdf')}
response = requests.post(url, files=files)
print(response.status_code)
print(response.json())
