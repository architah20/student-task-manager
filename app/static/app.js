const API = "/api/tasks";
const list = document.getElementById("task-list");
const empty = document.getElementById("empty");
const summary = document.getElementById("summary");
const form = document.getElementById("task-form");
const formError = document.getElementById("form-error");
let currentFilter = "";

async function request(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (response.status === 204) return null;
  const body = await response.json();
  if (!response.ok) {
    const message = body.errors ? Object.values(body.errors).join(", ") : body.error;
    throw new Error(message || "Request failed");
  }
  return body;
}

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function renderTask(task) {
  const item = el("li", "task" + (task.status === "done" ? " done" : ""));

  const info = el("div");
  info.appendChild(el("h3", "", task.title));
  if (task.description) info.appendChild(el("p", "", task.description));
  const meta = el("div", "meta");
  meta.appendChild(el("span", "badge", task.status));
  if (task.due_date) meta.appendChild(document.createTextNode("  Due: " + task.due_date));
  info.appendChild(meta);

  const actions = el("div", "actions");

  const toggle = el("button", "btn small", task.status === "done" ? "Undo" : "Complete");
  toggle.addEventListener("click", async () => {
    await request(`${API}/${task.id}`, {
      method: "PUT",
      body: JSON.stringify({ status: task.status === "done" ? "pending" : "done" }),
    });
    loadTasks();
  });

  const edit = el("button", "btn small", "Edit");
  edit.addEventListener("click", async () => {
    const title = prompt("Edit task title:", task.title);
    if (title === null) return;
    try {
      await request(`${API}/${task.id}`, { method: "PUT", body: JSON.stringify({ title }) });
      loadTasks();
    } catch (error) {
      alert(error.message);
    }
  });

  const remove = el("button", "btn small danger", "Delete");
  remove.addEventListener("click", async () => {
    if (!confirm("Delete this task?")) return;
    await request(`${API}/${task.id}`, { method: "DELETE" });
    loadTasks();
  });

  actions.append(toggle, edit, remove);
  item.append(info, actions);
  return item;
}

async function loadTasks() {
  const query = currentFilter ? `?status=${currentFilter}` : "";
  const tasks = await request(API + query);
  list.replaceChildren(...tasks.map(renderTask));
  empty.hidden = tasks.length > 0;

  const all = currentFilter ? await request(API) : tasks;
  const done = all.filter((t) => t.status === "done").length;
  summary.textContent = `${all.length} task(s), ${done} completed`;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  formError.hidden = true;
  try {
    await request(API, {
      method: "POST",
      body: JSON.stringify({
        title: document.getElementById("title").value,
        description: document.getElementById("description").value,
        due_date: document.getElementById("due_date").value || null,
      }),
    });
    form.reset();
    loadTasks();
  } catch (error) {
    formError.textContent = error.message;
    formError.hidden = false;
  }
});

document.querySelectorAll(".filter").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".filter").forEach((b) => b.classList.remove("active"));
    button.classList.add("active");
    currentFilter = button.dataset.filter;
    loadTasks();
  });
});

loadTasks();
