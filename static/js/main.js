document.addEventListener("DOMContentLoaded", () => {
  console.log("Frontend loaded.");

  // Helper: activate clicked button and deactivate siblings in same .tabs container
  const setActiveInGroup = (clickedBtn) => {
    const group = clickedBtn.parentElement;
    if (!group) return;
    const buttons = group.querySelectorAll("button.tab");
    buttons.forEach(b => b.classList.remove("active"));
    clickedBtn.classList.add("active");
  };

  const timeframeHidden = document.getElementById("time_range_input");
  const indicatorHidden = document.getElementById("indicator_input");

  // canonical timeframe values used on the page
  const timeframeValues = new Set(["1M", "3M", "6M", "1Y", "2Y"]);

  // Attach listeners to all .tab buttons (works for timeframe and indicator groups)
  document.querySelectorAll(".tabs").forEach(tabGroup => {
    tabGroup.querySelectorAll("button.tab").forEach(btn => {
      btn.addEventListener("click", (ev) => {
        ev.preventDefault();
        setActiveInGroup(btn);

        const val = btn.dataset && btn.dataset.value ? btn.dataset.value : btn.getAttribute("data-value");
        if (!val) return;

        // If value looks like a timeframe, set the timeframe hidden input.
        // Otherwise treat it as an indicator selection and set the indicator hidden input.
        if (timeframeValues.has(val) && timeframeHidden) {
          timeframeHidden.value = val;
        } else if (indicatorHidden) {
          indicatorHidden.value = val;
        }

        // NOTE: changes are sent to server when the user clicks a form submit button.
      });

      // keyboard friendly
      btn.addEventListener("keydown", (ev) => {
        if (ev.key === "Enter" || ev.key === " ") {
          ev.preventDefault();
          btn.click();
        }
      });
    });
  });

});
