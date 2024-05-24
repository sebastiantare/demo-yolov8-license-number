var buffer = [];

var socket = io('http://localhost:5000');

var waited = false;

const canvas = document.getElementById('image');
var ctx = canvas.getContext('2d');

var license_plates = {};

var rows_hashmap = {};

var frame_number = -1;
var frame_licenses = {};

socket.on('connect', function() {
  console.log("Connection has been succesfully established with socket.", socket.connected)
});

function addLicenseToTable(json_data) {
  var text = json_data['text'];
  var category = json_data['category'];
  var vehicle_type = 'Auto';
  //# 2: car, 3: motorbike, 5: bus, 6:train, 7: truck

  console.log(text);

  switch (category) {
    case '2':
      vehicle_type = "Auto";
    case '3':
      vehicle_type = "Moto";
    case '5':
      vehicle_type = "Bus";
    case '6':
      vehicle_type = "Tren";
    case '7':
      vehicle_type = "Camión";
  }

  if (text in license_plates) {
    license_plates[text] += 1;
  } else {
    license_plates[text] = 1;
  }

  // Improve visual confidence of scores.
  if (license_plates[text] < 5) return;

  const tableBody = document.getElementById('licensePlateTableBody');

  let targetRow = rows_hashmap[text];

  if (targetRow) {
    const countCell = targetRow.cells[2];
    countCell.textContent = license_plates[text];

    const categoryCell = targetRow.cells[3];
    categoryCell.textContent = vehicle_type;

  } else {
    const newRow = document.createElement('tr');

    const licensePlateCell = document.createElement('td');
    licensePlateCell.textContent = text;
    newRow.appendChild(licensePlateCell);

    const timestampCell = document.createElement('td');
    const now = new Date();
    timestampCell.textContent = now.toLocaleString();
    newRow.appendChild(timestampCell);

    const countCell = document.createElement('td');
    countCell.textContent = license_plates[text];
    newRow.appendChild(countCell);

    const categoryCell = document.createElement('td');
    categoryCell.textContent = vehicle_type;
    newRow.appendChild(categoryCell);

    tableBody.appendChild(newRow);
    rows_hashmap[text] = newRow;

    // Sort rows by datetime.
    var rows = tableBody.rows;

    var sortedRows = Array.from(rows).sort((a, b) => {
      var date1 = new Date(a.cells[1].textContent);
      var date2 = new Date(b.cells[1].textContent);
      return date2 - date1;
    });

    // Remove existing rows from table
    while (tableBody.firstChild) {
      tableBody.removeChild(tableBody.firstChild);
    }

    // Re-add rows in sorted order
    sortedRows.forEach(row => {
      tableBody.appendChild(row);
    });
  }
}

socket.on('detection', function(json_data) {

  var text = json_data['license_text'];
  var category = json_data['category'];
  var date = json_data['date'];
  var frame = json_data['frame'];

  console.log('new license', text, category, date, frame);

  frame_licenses[frame] = { 'text': text, 'category': parseInt(category) };

});

socket.on('response_back', function(data) {
  var image = data['stringData'];
  frame_number = data['frame'];

  if (frame_number in frame_licenses) addLicenseToTable(frame_licenses[frame_number]);

  buffer.push(image);
});

setInterval(function() {
  if (start && waited) {
    drawImage();
  }
}, 1000 / 24);

var start = false;

document.getElementById('startStreaming').addEventListener('click', function() {
  if (!start) socket.emit('image');
  if (!start) setTimeout(function() { waited = true }, 1000)
  start = true;
});

function drawImage() {
  if (buffer.length > 0) {
    var base64Image = buffer.shift();
    var img = new Image();
    img.onload = function() {
      canvas.width = img.width;
      canvas.height = img.height;
      ctx.drawImage(img, 0, 0);
    };
    img.src = base64Image;
  }
}
