
document.addEventListener("DOMContentLoaded", function () {

    const searchInput = document.getElementById("searchInput");
    const searchButton = document.getElementById("searchButton");
    const searchMessage = document.getElementById("searchMessage");
    const emptyState = document.getElementById("noBusinesses");

    function filterBusinesses() {
        const searchText = searchInput.value.trim().toLowerCase();
        const businesses = document.querySelectorAll(".business-card");
        let count = 0;

        businesses.forEach(function (business) {
            const businessDetails = business.innerText.toLowerCase();
            if (businessDetails.includes(searchText)) {
                business.style.display = "";
                count++;
            } else {
                business.style.display = "none";
            }
        });

        emptyState.hidden = count > 0;
        searchMessage.textContent = searchText
            ? count + " matching business(es) found."
            : "Showing all businesses.";
    }

    searchButton.addEventListener("click", filterBusinesses);

    searchInput.addEventListener("keydown", function (event) {
        if (event.key === "Enter") {
            filterBusinesses();
        }
    });
});
