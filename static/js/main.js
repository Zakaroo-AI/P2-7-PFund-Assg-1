document.addEventListener("DOMContentLoaded", () => {
  console.log("Frontend loaded.");
});

// Below is the code to handle custom file input buttons and display selected file names
const actualFileInput1 = document.getElementById("actual-file-input-1");
const actualFileInput2 = document.getElementById("actual-file-input-2");
const fileChosen1 = document.getElementById("file-name-1");
const fileChosen2 = document.getElementById("file-name-2");


actualFileInput1.addEventListener("change", function() {
  if (this.files.length > 0) {
    fileChosen1.textContent = this.files[0].name;
  } else {
    fileChosen1.textContent = "No file chosen";
  }
});

actualFileInput2.addEventListener("change", function() {
  if (this.files.length > 0) {
    fileChosen2.textContent = this.files[0].name;
  } else {
    fileChosen2.textContent = "No file chosen";
  }
});