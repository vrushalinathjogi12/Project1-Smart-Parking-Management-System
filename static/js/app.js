// handles AJAX calls for entry, exit, status, revenue
async function postJSON(url, data) {
  const resp = await fetch(url, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data)
  });
  return resp.json();
}

async function getJSON(url) {
  const resp = await fetch(url);
  return resp.json();
}

document.addEventListener("DOMContentLoaded", function(){
  const entryForm = document.getElementById("entryForm");
  const entryMsg = document.getElementById("entryMsg");
  const exitForm = document.getElementById("exitForm");
  const exitMsg = document.getElementById("exitMsg");
  const quickInfo = document.getElementById("quickInfo");
  const btnStatus = document.getElementById("btnStatus");
  const btnRevenue = document.getElementById("btnRevenue");
  const slotGrid = document.getElementById("slotGrid");
  const slotGridAdmin = document.getElementById("slotGridAdmin");

  async function refreshStatus() {
    try {
      const data = await getJSON("/api/status");
      // reload the page section by simply refreshing the page via fetch of index HTML partial is complex;
      // instead, do a lightweight UI update using quickInfo text for now:
      quickInfo.innerHTML = `<div>Occupied: ${data.occupied_count} | Free: ${data.free_count}</div>`;
      // reload full page if partial not present
      location.reload(); // simple strategy to show updated grid; acceptable for demo
    } catch (e) {
      console.error(e);
    }
  }

  entryForm && entryForm.addEventListener("submit", async function(e){
    e.preventDefault();
    const number = document.getElementById("entryNumber").value.trim();
    const vtype = document.getElementById("entryType").value;
    const vip = document.getElementById("entryVip").checked;
    entryMsg.innerText = "Processing...";
    try {
      const res = await postJSON("/api/entry", {number, vtype, vip});
      if (res.success) {
        entryMsg.innerHTML = `<div class="alert alert-success">Parked ${number} at slot ${res.vehicle.slot}</div>`;
        setTimeout(()=>location.reload(), 800);
      } else {
        entryMsg.innerHTML = `<div class="alert alert-danger">${res.error}</div>`;
      }
    } catch (err) {
      entryMsg.innerHTML = `<div class="alert alert-danger">Error</div>`;
    }
  });

  exitForm && exitForm.addEventListener("submit", async function(e){
    e.preventDefault();
    const number = document.getElementById("exitNumber").value.trim();
    exitMsg.innerText = "Processing...";
    try {
      const res = await postJSON("/api/exit", {number});
      if (res.success) {
        const r = res.record;
        exitMsg.innerHTML = `<div class="alert alert-success">Vehicle ${r.vehicle_number} exited from slot ${r.slot}. Fee: ₹ ${r.fee.toFixed(2)}</div>`;
        setTimeout(()=>location.reload(), 1200);
      } else {
        exitMsg.innerHTML = `<div class="alert alert-danger">${res.error}</div>`;
      }
    } catch (err) {
      exitMsg.innerHTML = `<div class="alert alert-danger">Error</div>`;
    }
  });

  btnStatus && btnStatus.addEventListener("click", refreshStatus);

  btnRevenue && btnRevenue.addEventListener("click", async function(){
    const res = await getJSON("/api/revenue");
    alert(`Date: ${res.date}\nVehicles: ${res.total_vehicles}\nRevenue: ₹ ${res.total_revenue}`);
  });
});
