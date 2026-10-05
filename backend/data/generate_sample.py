import csv, random
from pathlib import Path
random.seed(42)
path = Path(__file__).with_name('sample_claims.csv')
options = {
 'Insurance_Type':['Private','Government','Employer Sponsored'], 'Procedure_Category':['Imaging','Surgery','Laboratory','Consultation','Emergency','Therapy'], 'Diagnosis_Category':['Cardiology','Orthopedic','Respiratory','Neurology','General','Gastroenterology'], 'Prior_Authorization':['Yes','No'], 'Provider_Type':['Hospital','Clinic','Specialist Center'], 'Place_of_Service':['Inpatient','Outpatient','Emergency'], 'Submission_Method':['Electronic','Paper'], 'Claim_Type':['Professional','Institutional'], 'Network_Status':['In-Network','Out-of-Network'], 'Referral_Required':['Yes','No']}
headers=['Claim_ID']+list(options)+['Claim_Status','Claim_Amount']
with path.open('w', newline='', encoding='utf-8') as handle:
    writer=csv.DictWriter(handle, fieldnames=headers); writer.writeheader()
    for number in range(1, 601):
        row={'Claim_ID':f'CLM-{number:05d}'}
        for key, values in options.items(): row[key]=random.choice(values)
        score=0
        score += 2 if row['Prior_Authorization']=='Yes' else -1
        score += 1 if row['Network_Status']=='In-Network' else -1
        score += 1 if row['Submission_Method']=='Electronic' else 0
        score += 1 if row['Provider_Type']=='Hospital' else 0
        row['Claim_Status']='Approved' if score + random.randint(-2,2) >= 1 else 'Denied'
        row['Claim_Amount']=round(random.uniform(85, 18500), 2)
        writer.writerow(row)
print(path)
