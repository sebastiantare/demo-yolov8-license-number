var buffer = [];

var socket = io('http://localhost:5000');

var waited = false;

const canvas = document.getElementById('image');
var ctx = canvas.getContext('2d');

var license_plates = {};

var rows_hashmap = {};


socket.on('connect', function() {
  console.log("Connection has been succesfully established with socket.", socket.connected)
});

socket.on('license_plate', function(text) {

  if (text in license_plates) {
    license_plates[text] += 1;
  } else {
    license_plates[text] = 1;
  }

  const tableBody = document.getElementById('licensePlateTableBody');

  let targetRow = rows_hashmap[text];

  if (targetRow) {
    const countCell = targetRow.cells[2];
    countCell.textContent = license_plates[text];
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

});

socket.on('response_back', function(image) {
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
