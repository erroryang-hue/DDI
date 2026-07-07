import requests
url='http://127.0.0.1:8000/api/v1/analyze'
payload={
 'drug1':'Aspirin','drug2':'Warfarin','age':65,'weight':75,'dose1':500,'dose2':5,
 'start1':0,'start2':24,'interval1':24,'interval2':24,'poor_metabolizer':False
}
print('posting',payload)
r=requests.post(url,json=payload,timeout=10)
print('status',r.status_code)
print(r.text)
