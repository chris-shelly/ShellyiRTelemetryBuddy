import numpy as np
import boto3
import json
from decimal import Decimal


s3_client = boto3.client('s3')
dynamodb_resource = boto3.resource('dynamodb')
ssm_client = boto3.client('ssm','us-east-1')
dest_bucket_name_response = ssm_client.get_parameter(
        Name='/shelly-ir-telem/telem-output-bucket'
    )
dest_bucket_name = dest_bucket_name_response['Parameter']['Value']

table_response = ssm_client.get_parameter(
        Name='/shelly-ir-telem/stint-table'
    )
table_name = table_response['Parameter']['Value']
table = dynamodb_resource.Table(table_name)

#open the csv file
def lambda_handler(event, context): # need the csv filename, the source bucket and the destination bucket
    #initialize the S3 client

    #destination bucket name
    records_list = event['Records'][0]
    body = records_list['body']
    my_records = json.loads(body)
    #process the telemetry data to generate the Stint Report
    for record in my_records['Records']:
        #Retrieve the bucket name and file/key
        bucket_name = record['s3']['bucket']['name']
        key_name = record['s3']['object']['key']

        #download the file from S3 to the Lambda envt
        local_filename = key_name.split('/')[-1]
        print(local_filename)
        if len(local_filename.split('--')) > 1: #expecting our local filename to be split into three if it is formatted with a username
            print("username found")
            username = local_filename.split('--')[-2]
        else:
            username = "N_A"
        print(username)
        print("retrieving object from S3")
        response = s3_client.get_object(Bucket=bucket_name, Key=key_name.replace("+"," "))
        content = response['Body']

        #process the CSV file to generate a stint report
        print("processing CSV file")
        telem_text = str(content.read())
        telem_rows = telem_text.split("\\r\\n")
        
        telem_headers = telem_rows[9].split(",") #return the headers for the csv data as a list
        col_count = 0
        for col_header in telem_headers: #iterate through the headers to find the appropriate column index for LapLastLapTime and Lap
            if col_header == "LapLastLapTime":
                print(col_count)
                last_laptime_col = col_count
            if col_header == "Lap":
                print(col_count)
                lap_col = col_count
            col_count += 1
        
        driver = telem_rows[0].split(",")[1]
        car = telem_rows[1].split(",")[1] #car is described in the first row
        track = telem_rows[2].split(",")[1] #track is described in the second row
        sample_rate = int(telem_rows[6].split(",")[1]) #assuming sample rate is in hertz
        sample_units = telem_rows[6].split(",")[2] 
        print(f"{car} at {track}, {sample_rate} {sample_units}")
        
        sample_buffer = int(1.5*sample_rate) #540 samples, asssuming 360 samples/sec, use to retrieve laptimes after the lap is clocked
        
        out_lap = int(telem_rows[12].split(",")[lap_col]) #refer to lap col to get Laps
        lap_stack = [out_lap + 1]
        laptime_stack = []
        for ii in range(13,len(telem_rows[13:])):
            curr_lap = int(telem_rows[ii].split(",")[lap_col])
            if curr_lap > lap_stack[-1]:
                lap_stack.append(curr_lap)
                laptime_stack.append(float(telem_rows[ii+sample_buffer].split(",")[last_laptime_col])) #in the csv telemetry, "LastLapTime" is in column 122
        lap_stack.pop() #assume the last lap is just an outlap
        
        if len(laptime_stack) == 0:
            average_lap = 0
        else:
            average_lap = np.average(laptime_stack)
        
        #our stint report
        report = {
            "car": car,
            "track":  track,
            "laps": lap_stack,
            "laptimes": laptime_stack,
            "average lap": average_lap
        }
        print(report)
        
        #check the number of items in the table by scanning
        table_scan_response = table.scan()
        count = table_scan_response['Count']
        stint_id = count + 1
        
        #write the data to dynamodb table
        taple_putitem_response = table.put_item(
            Item={
                'Stint ID': stint_id,
                'Driver Name': driver,
                'Car': car,
                'Track': track,
                'Number of Laps': len(lap_stack),
                'Average Lap Time': Decimal(str(average_lap)),
                'Username':username
            }
            )
        
        
        #put the object to S3
        stint_filename = f"Stint Report-{local_filename}.txt"
        stint_filepath = "/tmp/" + stint_filename
        stint_file = open(stint_filepath,"w")
        stint_file.write(str(report))

        #upload the Stint report to the S3 bucket
        s3_client.put_object(Bucket=dest_bucket_name, Key=stint_filename,Body=str(report))
    return {
        "statusCode": 200,
        "body": f'Stint {stint_id} had an average laptime of {average_lap} and was saved in our system'
    }


