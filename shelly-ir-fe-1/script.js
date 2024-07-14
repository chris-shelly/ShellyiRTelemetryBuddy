const API_ENDPOINT = 'https://apigatewayendpointhere'

document.getElementById('uploadButton').addEventListener('click', function() {
    var fileInput = document.getElementById('csvtelemfile');
    
    console.log(fileInput.files[0])
    // const file = fileInput.files[0];

    if (typeof fileInput.files[0] == 'undefined') {
        console.log('no file')
        alert('Please select a file first!');
        return;
    }
    var file = fileInput.files[0]
    // Request a pre-signed URL from your backend
    //replace the /generate-presigned-url with the API Gateway Endpoint
    fetch(API_ENDPOINT, {
        method: 'POST',
        headers: {
            'Authorization': document.cookie,
            'Content-Type': 'application/json',
        },
        // Include any necessary data for the backend, such as file name and type
        body: JSON.stringify({
            fileName: file.name,
            fileType: file.type,
        }),
    })
    .then(response => response.json())
    .then(data => {
        // Use the pre-signed URL to upload the file directly to S3
        console.log(data.body)
        var presignedUrl = data.body;
        return fetch(presignedUrl, {
            method: 'PUT',
            body: file,
        });
    })
    .then(uploadResponse => {
        if (uploadResponse.ok) {
            alert('Upload successful');
        } else {
            throw new Error('Upload failed');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error during file upload');
    });
});

document.getElementById('viewStints').addEventListener('click', function() {
    // Your API response
    fetch(API_ENDPOINT, {
        method: 'GET',
        headers: {
            'Authorization': document.cookie,
        }
    })
    .then(apiResponse => apiResponse.json())
    .then(data =>  {
        console.log(data);
        if (data.statusCode === 200) {
            deleteTable();
            createTable(data.body);
          } else {
            console.error('Failed to load data');
          }
    })
    // Function to create and populate the table
    function createTable(data) {
      const table = document.createElement('table');
      const thead = document.createElement('thead');
      const tbody = document.createElement('tbody');
      const headers = ["Car", "Track", "Driver Name", "Stint ID", "Number of Laps", "Average Lap Time"];
  
      let row = thead.insertRow();
      for (let header of headers) {
        let th = document.createElement('th');
        th.textContent = header;
        row.appendChild(th);
      }
  
      for (let item of data) {
        let row = tbody.insertRow();
        for (let key of headers) {
          let cell = row.insertCell();
          cell.textContent = item[key];
        }
      }
  
      table.appendChild(thead);
      table.appendChild(tbody);
      document.getElementById('data-table').appendChild(table);
    }
  
    // Check if the API returned a successful status code before creating the table
    function deleteTable() {
        // Select the div where the table is appended
        const dataTableDiv = document.getElementById('data-table');
        
        // Check if there is a table inside the div
        const table = dataTableDiv.querySelector('table');
        
        // If a table exists, remove it
        if (table) {
          dataTableDiv.removeChild(table);
          console.log('Existing table has been removed. Re-generating table now.')
        } else {
          console.log('No table found to delete. Generating Table for the first time');
        }
      }
  });
  
