const fileList = document.querySelector(".file-list");
const fileBrowseButton = document.querySelector(".file-browse-button");
const fileBrowseInput = document.querySelector(".file-browse-input");
const fileUploadBox = document.querySelector(".file-upload-box");
const fileCompletedStatus = document.querySelector(".file-completed-status");
const uploadForm = document.getElementById("upload-form");
const formSubmitButton = document.querySelector(".main-btn");

let totalFiles = new Array;
let totalFileCount = 0;
let completedFileCount = 0;
let fileIndexIdentifierMap = {};
let canceledFilesIds = [];

// Function to create HTML for each file item
const createFileItemHTML = (file, uniqueIdentifier) => {
    // Extracting file name, size, and extension
    var {name, size} = file;
    const extension = name.split(".").pop();
    // Rise alert for unaccepted types
    if (!fileBrowseInput.accept.replace(" ", "").split(",").includes("." + extension)) {
        alert(`file must either be '.nii' of '.dcm\nSkipping file: "${name}"`);
        return;
    }
    // Trim long filename
    if (name.length > 40) {
        name = name.substr(0, 20) + '...' + name.substr(-20);
    }
    const formattedFileSize = size >= 1024 * 1024 ? `${(size / (1024 * 1024)).toFixed(2)} MB` : `${(size / 1024).toFixed(2)} KB`;

    // Generating HTML for file item
    return `<li class="file-item" id="file-item-${uniqueIdentifier}">
                <div class="file-extension">.${extension}</div>
                <div class="file-content-wrapper">
                <div class="file-content">
                    <div class="file-details">
                    <h5 class="file-name">${name}</h5>
                    <div class="file-info">
                        <small class="file-size">${formattedFileSize}</small>
                        <small class="file-divider">•</small>
                        <small class="file-status">Selected</small>
                    </div>
                    </div>
                    <button class="cancel-button">
                    <i class="bx bx-x"></i>
                    </button>
                </div>
                <div class="file-progress-bar">
                    <div class="file-progress"></div>
                </div>
                </div>
            </li>`;
}

// Function to handle file uploading
// const handleFileUploading = (form) => {
//     const files = form.elements.namedItem("file-browse-input").files;
//     files.forEach((file, index) => {
//         const xhr = new XMLHttpRequest();
//         // Adding progress event listener to the ajax request
//         xhr.upload.addEventListener("progress", (e) => {
//             // Updating progress bar and file size element
//             const fileProgress = document.querySelector(`#file-item-${uniqueIdentifier} .file-progress`);
//             const fileSize = document.querySelector(`#file-item-${uniqueIdentifier} .file-size`);
            
//             // Formatting the uploading or total file size into KB or MB accordingly
//             const formattedFileSize = file.size >= 1024 * 1024  ? `${(e.loaded / (1024 * 1024)).toFixed(2)} MB / ${(e.total / (1024 * 1024)).toFixed(2)} MB` : `${(e.loaded / 1024).toFixed(2)} KB / ${(e.total / 1024).toFixed(2)} KB`;
            
//             const progress = Math.round((e.loaded / e.total) * 100);
//             fileProgress.style.width = `${progress}%`;
//             fileSize.innerText = formattedFileSize;
//         });
//     });
    
//     // Opening connection to the server API endpoint "api.php" and sending the form data
//     xhr.open("POST", "{{ url_for("upload") }}", true);
//     xhr.send(uploadForm.formData);

//     return xhr;
// }

// Function to handle file uploading
const handleFileUploading = (file, uniqueIdentifier, subject_id, image_id) => {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    formData.append("file", file);
    formData.append("subject_id", subject_id);
    formData.append("image_id", image_id);
    // Adding progress event listener to the ajax request
    xhr.upload.addEventListener("progress", (e) => {
        // Updating progress bar and file size element
        const fileProgress = document.querySelector(`#file-item-${uniqueIdentifier} .file-progress`);
        const fileSize = document.querySelector(`#file-item-${uniqueIdentifier} .file-size`);
        // Formatting the uploading or total file size into KB or MB accordingly
        const formattedFileSize = file.size >= 1024 * 1024  ? `${(e.loaded / (1024 * 1024)).toFixed(2)} MB / ${(e.total / (1024 * 1024)).toFixed(2)} MB` : `${(e.loaded / 1024).toFixed(2)} KB / ${(e.total / 1024).toFixed(2)} KB`;
        const progress = Math.round((e.loaded / e.total) * 100);
        fileProgress.style.width = `${progress}%`;
        fileSize.innerText = formattedFileSize;
    });
    // Opening connection to the server API endpoint "upload" and sending the form data
    xhr.open("POST", "{{ url_for('upload') }}", true);
    xhr.send(formData);
    return xhr;
}

// Update file status text and change color of it 
const updateFileStatus = (FileItem ,status, color) => {
    FileItem.querySelector(".file-status").innerText = status;
    FileItem.querySelector(".file-status").style.color = color;
}

// Function to create html of selected files
const createHTMLofSelectedFiles = ([...files]) => {
    // Check if no files are selected
    if(files.length === 0) {
        return;
    }
    totalFileCount += files.length;

    files.forEach((file, index) => {
        const uniqueIdentifier = Date.now() + index;
        fileIndexIdentifierMap[index] = uniqueIdentifier;
        const fileItemHTML = createFileItemHTML(file, uniqueIdentifier);
        // Skip file if invalid
        if (!fileItemHTML) {
            totalFileCount--;
            return;
        }
        // Inserting each file item into file list
        fileList.insertAdjacentHTML("afterbegin", fileItemHTML);
        const currentFileItem = document.querySelector(`#file-item-${uniqueIdentifier}`);

        const cancelFileUploadButton = currentFileItem.querySelector(".cancel-button");
        // Handling cancellation of file upload
        cancelFileUploadButton.addEventListener("click", () => {
            canceledFilesIds.push(currentFileItem.id); // mark file as cancelled
            updateFileStatus(currentFileItem, "Cancelled", "#E3413F");
            cancelFileUploadButton.remove();
            totalFileCount -= 1;
            fileCompletedStatus.innerText = `${completedFileCount} / ${totalFileCount} files uploaded`;
            if (totalFileCount === 0){
                formSubmitButton.setAttribute("disabled", "");
            }
        });
        
    });
    
    if (totalFileCount > 0) {
        fileCompletedStatus.innerText = `${completedFileCount} / ${totalFileCount} files uploaded`;
    }
}
            
// Function to upload selected files
const uploadSelectedFiles = () => {
    const subject_id = uploadForm.elements.namedItem("subject_id").value;
    const image_id = uploadForm.elements.namedItem("image_id").value;
    // Check if no files are selected
    if(totalFiles.length === 0) {
        return;
    }
    
    totalFiles.forEach((file, index) => {
        const uniqueIdentifier = fileIndexIdentifierMap[index];
        // Cancel html creation for invalid file
        if (canceledFilesIds.includes(uniqueIdentifier)) {
            return;
        }
        const currentFileItem = document.querySelector(`#file-item-${uniqueIdentifier}`);
        // Check if file was already uploaded
        if (currentFileItem.querySelector(".file-status").innerText == "Uploaded") {
            return;
        }
        const cancelFileUploadButton = currentFileItem.querySelector(".cancel-button");
        const xhr = handleFileUploading(file, uniqueIdentifier, subject_id, image_id);
        
        // Handling cancellation of file upload
        cancelFileUploadButton.addEventListener("click", () => {
            xhr.abort();
            updateFileStatus(currentFileItem, "Cancelled", "#E3413F");
            cancelFileUploadButton.remove();
            totalFileCount--;
        });
        xhr.addEventListener("readystatechange", () => {
            // Handling completion of file upload
            if(xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
                completedFileCount++;
                cancelFileUploadButton.remove();
                updateFileStatus(currentFileItem, "Uploaded", "#00B125");
                fileCompletedStatus.innerText = `${completedFileCount} / ${totalFileCount} files uploaded`;
            }
        });
        // Show Alert if there is any error occured during file uploading
        xhr.addEventListener("error", () => {
            updateFileStatus("Error", "#E3413F");
            alert("An error occurred during the file upload!");
        });
    });
    fileCompletedStatus.innerText = `${completedFileCount} / ${totalFileCount} files uploaded`;
}

// Function to send predict request
const sendPredictRequest = () => {
    // Check if no files are selected
    if(totalFiles.length === 0) {
        return
    };
    const subject_id = uploadForm.elements.namedItem("subject_id").value;
    const image_id = uploadForm.elements.namedItem("image_id").value;
    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    for (const file of totalFiles) {
        formData.append("file", file)
    }
    formData.set("subject_id", subject_id);
    formData.set("image_id", image_id);

    // Handle requet progress event
    xhr.addEventListener("progress", (e) => {
        const predictProgress = document.querySelector(".predict-progress");
        const pct = document.querySelector(".predict-progress-pct");
        const progress = Math.round((e.loaded / e.total) * 100);
        predictProgress.style.width = `${progress}%`;
        pct.innerText = `${progress}%`;
    });
    // Handling completion of file upload
    xhr.addEventListener("readystatechange", () => {
        if(xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
            let response = xhr.response;
            debugger;
            response = JSON.parse(response);
            document.location.href=response.redirect;
            // xhr.open("POST", response.post, true);
            // xhr.send({data: response.data});
        };
    });
    // Show Alert if there is any error occured during file uploading
    xhr.addEventListener("error", () => {
        const predictProgressStatus = document.querySelector(".predit-progress-status");
        predictProgressStatus.innerText = "Error";
        predictProgressStatus.style.color = "#E3413F";
        predictProgress.style.color = "#E3413F";
        pct.style.color = "#E3413F";
        alert("An error occurred during while processing the files!");
    });

    // Send predict request
    xhr.open("POST", "{{ url_for('submit') }}", true);
    xhr.send(formData);
}

// Function to handle file drop event
fileUploadBox.addEventListener("drop", (e) => {
    e.preventDefault();
    createHTMLofSelectedFiles(e.dataTransfer.files);
    totalFiles.push(...e.dataTransfer.files);
    fileUploadBox.classList.remove("active");
    fileUploadBox.querySelector(".file-instruction").innerText = "Drag files here or";
    if (totalFileCount > 0) {
        fileBrowseButton.style.display = "inline";
        formSubmitButton.removeAttribute("disabled");
    };
});

// Function to handle file dragover event
fileUploadBox.addEventListener("dragover", (e) => {
    e.preventDefault();
    fileUploadBox.classList.add("active");
    fileUploadBox.querySelector(".file-instruction").innerText = "Release to upload";
    fileBrowseButton.style.display = "none";
});

// Function to handle file dragleave event
fileUploadBox.addEventListener("dragleave", (e) => {
    e.preventDefault();
    fileUploadBox.classList.remove("active");
    fileUploadBox.querySelector(".file-instruction").innerText = "Drag files here or";
    fileBrowseButton.style.display = "inline";
});

fileBrowseInput.addEventListener("change", (e) => {
    createHTMLofSelectedFiles(e.target.files);
    totalFiles.push(...e.target.files);
    if (totalFileCount > 0) {
        fileBrowseButton.style.display = "inline";
        formSubmitButton.removeAttribute("disabled");
    };
});
fileBrowseButton.addEventListener("click", () => fileBrowseInput.click());
formSubmitButton.addEventListener("click", (e) => {
    // Upload the form to {{ url_for("upload") }}
    uploadSelectedFiles(e.target.form);
    // Send post request to {{ "/predict" }}
    formSubmitButton.style.display = "none";
    document.querySelector(".predict-progress-bar").style.display = "contents";
    sendPredictRequest(e.target.form);
})