const fileList = document.querySelector(".file-list");
const fileBrowseButton = document.querySelector(".file-browse-button");
const fileBrowseInput = document.querySelector(".file-browse-input");
const fileUploadBox = document.querySelector(".file-upload-box");
const fileCompletedStatus = document.querySelector(".file-completed-status");
const uploadForm = document.getElementById("upload-form");
const formSubmitButton = document.querySelector(".main-btn");

let totalFiles = 0;
let completedFiles = 0;
let fileIndexIdentifierMap = {};
let cancelledFiles = [];

// Function to create HTML for each file item
const createFileItemHTML = (file, uniqueIdentifier) => {
    // Extracting file name, size, and extension
    const {name, size} = file;
    const extension = name.split(".").pop();
    // Trim long filename
    if (name.length > 40) {
        name = name.substr(0, 20) + '...' + name.substr(-20);
    }
    const formattedFileSize = size >= 1024 * 1024 ? `${(size / (1024 * 1024)).toFixed(2)} MB` : `${(size / 1024).toFixed(2)} KB`;

    // Generating HTML for file item
    return `<li class="file-item" id="file-item-${uniqueIdentifier}">
                <div class="file-extension">${extension}</div>
                <div class="file-content-wrapper">
                <div class="file-content">
                    <div class="file-details">
                    <h5 class="file-name">${name}</h5>
                    <div class="file-info">
                        <small class="file-size">${formattedFileSize}</small>
                        <small class="file-divider">•</small>
                        <small class="file-status"></small>
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
        if(files.length === 0) return; // Check if no files are selected
        totalFiles += files.length;
    
        files.forEach((file, index) => {
            const uniqueIdentifier = Date.now() + index;
            fileIndexIdentifierMap[index] = uniqueIdentifier;
            const fileItemHTML = createFileItemHTML(file, uniqueIdentifier);
            // Inserting each file item into file list
            fileList.insertAdjacentHTML("afterbegin", fileItemHTML);
            const currentFileItem = document.querySelector(`#file-item-${uniqueIdentifier}`);
    
            const cancelFileUploadButton = currentFileItem.querySelector(".cancel-button");
            // Handling cancellation of file upload
            cancelFileUploadButton.addEventListener("click", () => {
                cancelledFiles.append(currentFileItem.id); // mark file as cancelled
                updateFileStatus(currentFileItem, "Cancelled", "#E3413F");
                totalFiles -= 1;
                cancelFileUploadButton.remove();
            });
            
        });
}
            
// Function to upload selected files
const uploadSelectedFiles = (form) => {
    const files = form.elements.namedItem("file-browse-input").files;
    const subject_id = form.elements.namedItem("subject_id").value;
    const image_id = form.elements.namedItem("image_id").value;
    if(files.length === 0) return; // Check if no files are selected
    totalFiles += files.length;
    files.forEach((file, index) => {
        if (uniqueIdentifier in cancelledFiles) {
            return;
        };
        const uniqueIdentifier = fileIndexIdentifierMap[index];
        const currentFileItem = document.querySelector(`#file-item-${uniqueIdentifier}`);
        const cancelFileUploadButton = currentFileItem.querySelector(".cancel-button");
        const xhr = handleFileUploading(file, uniqueIdentifier, subject_id, image_id);
        
        // Handling cancellation of file upload
        cancelFileUploadButton.addEventListener("click", () => {
            xhr.abort();
            updateFileStatus(currentFileItem, "Cancelled", "#E3413F");
            cancelFileUploadButton.remove();
            totalFiles--;
        });
        xhr.addEventListener("readystatechange", () => {
            // Handling completion of file upload
            if(xhr.readyState === XMLHttpRequest.DONE && xhr.status === 200) {
                completedFiles++;
                cancelFileUploadButton.remove();
                updateFileStatus(currentFileItem, "Completed", "#00B125");
                fileCompletedStatus.innerText = `${completedFiles} / ${totalFiles} files completed`;
            }
        });
        // Show Alert if there is any error occured during file uploading
        xhr.addEventListener("error", () => {
            updateFileStatus("Error", "#E3413F");
            alert("An error occurred during the file upload!");
        });
    });
    fileCompletedStatus.innerText = `${completedFiles} / ${totalFiles} files completed`;
}

// Function to handle file drop event
fileUploadBox.addEventListener("drop", (e) => {
    e.preventDefault();
    createHTMLofSelectedFiles(e.dataTransfer.files);
    fileUploadBox.classList.remove("active");
    fileUploadBox.querySelector(".file-instruction").innerText = "Drag files here or";
    fileBrowseButton.style.display = "inline";
    formSubmitButton.removeAttribute("disabled");
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
    formSubmitButton.removeAttribute("disabled");
});
fileBrowseButton.addEventListener("click", () => fileBrowseInput.click());
formSubmitButton.addEventListener("click", (e) => {
    uploadSelectedFiles(e.target.form);
})