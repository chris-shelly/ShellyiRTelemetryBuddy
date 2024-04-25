# ShellyiRTelemetryBuddy
Serverless AWS Web App for summarized iRacing Telemetry reports. This allows iRacing drivers and crew chiefs to get a quick, high level summary of what their performance was on track. Without this app, these users would have had to setup a telemetry workbook in Motec and/or copy, paste, and transform their telemetry data in Excel. 

Users in the app can upload their iRacing telemetry files as CSV files. These telemetry files can hold data for each stint, a distinct number of laps that the driver drove. The fields in the telemetry files include Lap Times, Speed, Air Temeperature, Throttle Usage, Brake Usage, Steering, and more. Users can view a summary of each telemetry file that they've uploaded, letting them know the Number of Laps Completed and the Average Lap.

![Shelly iR Telem Buddy 1 (1)](https://github.com/chris-shelly/ShellyiRTelemetryBuddy/assets/117383781/cbc96191-3885-4d86-be18-598c79a086c5)

Potential next steps for this project in the future would be:
- Parsing the telemetry files in their original IBT format (telemetry files come from iRacing as an IBT, but they are not human readable in this form), which would reduce time for file uplaods, reduce total file sizes for storage in S3, and save the users time as they wouldn't need to use Mu or a similar tool files to CSVs.
- Vehicle Dynamics analysis to support setup building.
- - Visualizations of Driver Inputs
- - System Dynamics of Suspension Systems
- - Aerodynamic Analysis
- Setting Target lap times based on track conditions (weather, track state) and existing race data
- Sharing stints with other users
- - Average Lap-time challenges/competitions
