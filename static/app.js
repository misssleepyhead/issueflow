
async function loadIssues() {
    // 1. Call GET /issues
    const response = await fetch("/issues");

    // 2. Check for HTTP errors
    if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
    }

    // 3. Convert JSON response into JavaScript object
    const data = await response.json();

    // 4. Extract issues array
    const issues = data.issues;

    // 5. Check the data in the browser console
    console.log(issues);


    const tbody = document.querySelector("#issues-body");
    // Clear its existing rows before displaying new data
    tbody.replaceChildren()

    for (const issue of issues) {
        const row = document.createElement("tr");
        const id_cell = document.createElement("td");
        const title_cell = document.createElement("td");
        const status_cell = document.createElement("td");

        id_cell.textContent = issue.id;
        title_cell.textContent = issue.title;
        status_cell.textContent = issue.status;

        // Append all three cells to the <tr>
        row.appendChild(id_cell);
        row.appendChild(title_cell);
        row.appendChild(status_cell);

        tbody.appendChild(row);
    }

}

loadIssues().catch(error => {
    console.error(error);
    document.querySelector("#message").textContent =
        "Failed to load issues";
});



document.querySelector("#create-form").addEventListener(
    "submit",
    async function (event) {
        event.preventDefault();
        const titleInput = document.querySelector("#issue-title");
        const title = titleInput.value.trim();
        console.log("Submitting title:", title);

        if (!title) {
            document.querySelector("#message").textContent = "Please enter an issue title";
            return;
        }

        try {

            const response = await fetch("/issues", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ title: title })
            });
            console.log("POST status:", response.status);

            if (!response.ok) {
                const errorBody = await response.text();
                console.error("Server response:", errorBody);
                throw new Error(`Response status: ${response.status}`);
            }
            const createdIssue = await response.json();
            console.log("Created Issue:", createdIssue);

            // clear the input after successful creation
            titleInput.value = "";

            // refresh the issues table
            await loadIssues();

            document.querySelector("#message").textContent = "Issue created successfully";
        } catch (error) {
            console.error(error);
            document.querySelector("#message").textContent = "Failed to create issue";
        }


    }
);
