const apiBaseUrl = "https://7ddf84aykc.execute-api.us-east-1.amazonaws.com/prod";

// Function to search for photos
async function searchPhotos() {
    const query = document.getElementById("search-query").value;
    if (!query) {
        alert("Please enter a search term.");
        return;
    }

    try {
        const response = await fetch(`${apiBaseUrl}/search?q=${encodeURIComponent(query)}`, {
            method: "GET",
            headers: {
                "Content-Type": "application/json",
            },
        });
        const result = await response.json();

        if (result.data && result.data.length > 0) {
            displayResults(result.data);
        } else {
            alert("No photos found for the search term.");
        }
    } catch (error) {
        console.error("Error searching photos:", error);
        alert("An error occurred while searching for photos.");
    }
}

// Function to display search results
function displayResults(photoUrls) {
    const resultsDiv = document.getElementById("search-results");
    resultsDiv.innerHTML = ""; // Clear previous results

    photoUrls.forEach((url) => {
        const img = document.createElement("img");
        img.src = url;
        img.alt = "Photo";
        img.style = "margin: 10px; width: 200px; height: auto;";
        resultsDiv.appendChild(img);
    });
}

// Function to upload a new photo
async function uploadPhoto(event) {
    event.preventDefault();
    const photoInput = document.getElementById("photo-file");
    const customLabels = document.getElementById("custom-labels").value;

    if (!photoInput.files.length) {
        alert("Please select a photo to upload.");
        return;
    }

    const photoFile = photoInput.files[0];
    const formData = new FormData();
    formData.append("file", photoFile);
    formData.append("x-amz-meta-customLabels", customLabels);

    try {
        const response = await fetch(`${apiBaseUrl}/photos`, {
            method: "PUT",
            body: formData,
        });

        if (response.ok) {
            alert("Photo uploaded successfully.");
            document.getElementById("upload-form").reset();
        } else {
            alert("Failed to upload photo.");
        }
    } catch (error) {
        console.error("Error uploading photo:", error);
        alert("An error occurred while uploading the photo.");
    }
}
