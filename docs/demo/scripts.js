var video = document.querySelector("#video-webcam");
var snapshot = document.querySelector('#snapshot');
var btnOpenCamera = document.querySelector("#open-camera");
var btnTakeSnapshot = document.querySelector("#take-snapshot");
var resultRecognition = document.querySelector("#result-recognition");
var resultRecognitionBody = document.querySelector("#result-recognition #alert-body");

initPage()

function initPage(){
    video.style.display = "none"
    snapshot.style.display = "none"
    btnOpenCamera.style.display = "block"
    btnTakeSnapshot.style.display = "none"
    resultRecognition.style.display = "none"
}

function openCamera() {
    // minta izin user
    navigator.getUserMedia = navigator.getUserMedia || navigator.webkitGetUserMedia || navigator.mozGetUserMedia || navigator.msGetUserMedia || navigator.oGetUserMedia;

    // jika user memberikan izin
    if (navigator.getUserMedia) {
        video.style.display = 'block';
        snapshot.innerHTML = '';
        snapshot.style.display = "none";
        btnOpenCamera.style.display = "none";
        btnTakeSnapshot.style.display = "block";
        resultRecognition.style.display = "none";

        // jalankan fungsi handleVideo, dan videoError jika izin ditolak
        navigator.getUserMedia({ video: true }, handleVideo, videoError);
    }
}


// fungsi ini akan dieksekusi jika  izin telah diberikan
function handleVideo(stream) {
    video.srcObject = stream;
}

// fungsi ini akan dieksekusi kalau user menolak izin
function videoError(e) {
    // do something
    alert("Izinkan menggunakan webcam untuk demo!")
}

function takeSnapshot() {
    // buat element img
    var img = document.createElement('img');
    img.classList.add('img-fluid'); // Menambah kelas img-fluid
    var context;

    // ambil ukuran video
    var width = video.offsetWidth, height = video.offsetHeight;

    // buat elemen canvas
    canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;

    // ambil gambar dari video dan masukan
    // ke dalam canvas
    context = canvas.getContext('2d');
    context.drawImage(video, 0, 0, width, height);

    // render hasil dari canvas ke elemen img
    img.src = canvas.toDataURL('image/png');
//    document.body.appendChild(img);

    // Letakkan gambar dalam jumbotron

    snapshot.innerHTML = ''; // Hapus konten sebelumnya jika ada
    snapshot.appendChild(img);
    snapshot.style.display = 'block';

    video.style.display = 'none';
    btnOpenCamera.style.display = "block";
    btnTakeSnapshot.style.display = "none";

    var tracks = video.srcObject.getTracks();
    tracks.forEach(track => track.stop());

    recognizeFace(img.src);
}


function displayFileNames() {
    var input = document.getElementById('imageInput');
    var fileNamesContainer = document.getElementById('fileNames');

    // Clear previous file names
    fileNamesContainer.innerHTML = '';

    // Display selected file names
    for (var i = 0; i < input.files.length; i++) {
        var fileName = input.files[i].name;
        var fileNameElement = document.createElement('p');
        fileNameElement.textContent = fileName;
        fileNamesContainer.appendChild(fileNameElement);
    }
}

var baseUrl = 'https://face-recognition-sg4u.onrender.com/v1';

function registerFace() {
    var fileInput = document.getElementById('imageInput');
    var textInput = document.getElementById('textInput');

    // Check if files are selected
    if (fileInput.files.length === 0) {
        showModal("error", 'Please select at least one image file.');
        return;
    }

    // Create FormData object
    var formData = new FormData();

    // Append files to FormData
    for (var i = 0; i < fileInput.files.length; i++) {
        formData.append('files', fileInput.files[i], fileInput.files[i].name);
    }

    // Construct URL with parameters
    var urlWithParams = `${baseUrl}/register?name=${encodeURIComponent(textInput.value)}`;

    // Create requestOptions
    var requestOptions = {
        method: 'POST',
        body: formData,
        redirect: 'follow'
    };

    fetch(urlWithParams, requestOptions)
    .then(response => {
        if (!response.ok) {
            console.error('Failed to upload image.');
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
        showModal(data.status, data.message);
    })
    .catch(error => {
        console.error('Fetch error:', error);
        showModal("error", error.message);
    });
}

function recognizeFace(imageData) {
    // Validate the image format (assuming it's a data URL)
    if (!isValidImageFormat(imageData)) {
        console.error('Invalid image format.');
        alert('Invalid image format.');
        return;
    }

    // Construct the FormData object
    var formData = new FormData();
    formData.append('file', dataURItoBlob(imageData), 'snapshot.png');

    // Construct the URL for your server endpoint
    var url = `${baseUrl}/recognize`; // Replace with your actual API endpoint

    // Create requestOptions for the fetch API
    var requestOptions = {
        method: 'POST',
        body: formData,
        redirect: 'follow'
    };

    // Make the fetch request
    fetch(url, requestOptions)
    .then(response => {
        if (!response.ok) {
            console.error('Failed to upload image.');
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data.data);
        showModal(data.status, data.message);

        if (data.data) {
            resultRecognitionBody.innerHTML = ""
            resultRecognition.style.display = "block"
            var resultList = document.createElement("ul");
            resultList.className = "result-list";

            for (var i = 0; i < data.data.length; i++) {
                // Create a list item for each result
                var listItem = document.createElement("li");
                listItem.innerHTML = data.data[i][0];

                // Append the list item to the unordered list
                resultList.appendChild(listItem);

                console.log("result", data.data[i][0]);
            }

            // Append the unordered list to the result container
            resultRecognitionBody.appendChild(resultList);
        }
    })
    .catch(error => {
        console.error('Fetch error:', error);
        showModal("error", error.message);
    });
}

// Validate image format (for simplicity, check if it's a PNG image)
function isValidImageFormat(dataURI) {
    return dataURI.startsWith('data:image/png');
}

// Convert a data URL to a Blob
function dataURItoBlob(dataURI) {
    var byteString = atob(dataURI.split(',')[1]);
    var ab = new ArrayBuffer(byteString.length);
    var ia = new Uint8Array(ab);
    for (var i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
    }
    return new Blob([ia], { type: 'image/jpeg' });
}

function showModal(status, message) {
    $('#modal-container .modal-body').text(message);
    $('#modal-container').modal('show');
    $('#modal-container #modal-title').text(capitalizeFirstLetter(status));
}

function capitalizeFirstLetter(str) {
    return str.charAt(0).toUpperCase() + str.slice(1);
}