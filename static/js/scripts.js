// For Donor interface
document.getElementById("donate-form").addEventListener("submit", async (event) => {
    event.preventDefault();
  
    const formData = new FormData(event.target);
  
    const response = await fetch("/donate", {
      method: "POST",
      body: formData,
    });
  
    const result = await response.json();
    alert(result.message);
    event.target.reset();
    loadDonatedItems();
  });
  
  // Load Donated Items
  async function loadDonatedItems() {
    const response = await fetch("/donated-items");
    const items = await response.json();
  
    const container = document.getElementById("donated-items-container");
    container.innerHTML = "";
  
    items.forEach((item) => {
      const div = document.createElement("div");
      div.className = "item";
      div.innerHTML = `
        <img src="${item.image}" alt="${item.title}">
        <h3>${item.title}</h3>
        <p>${item.description}</p>
        <p><strong>Condition:</strong> ${item.condition}</p>
        <p><strong>Category:</strong> ${item.category}</p>
      `;
      container.appendChild(div);
    });
  }
  
  // For Viewer interface (Load Available Items)
  async function loadAvailableItems() {
    const response = await fetch("/items");
    const items = await response.json();
  
    const container = document.getElementById("items-container");
    container.innerHTML = "";
  
    items.forEach((item) => {
      const div = document.createElement("div");
      div.className = "item";
      div.innerHTML = `
        <img src="${item.image}" alt="${item.title}">
        <h3>${item.title}</h3>
        <p>${item.description}</p>
        <p><strong>Condition:</strong> ${item.condition}</p>
        <p><strong>Category:</strong> ${item.category}</p>
        <button onclick="requestItem('${item.title}')">Request Item</button>
      `;
      container.appendChild(div);
    });
  }
  
  // Request Item (Viewer makes request)
  async function requestItem(itemTitle) {
    const response = await fetch("/request-item", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ itemTitle }),
    });
  
    const result = await response.json();
    alert(result.message);
  }
  
  // Load items on page load (for viewer)
  if (window.location.pathname === "/viewer") {
    loadAvailableItems();
  } else if (window.location.pathname === "/donor") {
    loadDonatedItems();
  }
  