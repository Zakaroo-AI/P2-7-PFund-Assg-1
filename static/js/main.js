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

function setupPlotControls(plot_id) {
    var gd = document.getElementById(plot_id);
    if (!gd) return;

    var MAX_CHECKBOXES = 40;

    // Save original shapes & annotations for Max Profit toggle
    try {
        gd._orig_shapes = gd.layout && gd.layout.shapes ? JSON.parse(JSON.stringify(gd.layout.shapes)) : [];
        gd._orig_annos  = gd.layout && gd.layout.annotations ? JSON.parse(JSON.stringify(gd.layout.annotations)) : [];
    } catch (e) {
        gd._orig_shapes = [];
        gd._orig_annos  = [];
    }

    var ctrl = document.createElement('div');
    ctrl.id = plot_id + '-controls';
    ctrl.style.margin = '8px 0';
    ctrl.style.fontFamily = 'Arial, sans-serif';
    ctrl.style.fontSize = '13px';

    var toggleables = [];

    // Select all / Clear all buttons
    var btnAll = document.createElement('button');
    btnAll.textContent = 'Select all';
    btnAll.style.marginRight = '8px';
    btnAll.onclick = function(e) {
        e.preventDefault();
        toggleables.forEach(function(entry) {
            Plotly.restyle(gd, {'visible': true}, entry.indices);
            entry.checkbox.checked = true;
        });
    };

    var btnNone = document.createElement('button');
    btnNone.textContent = 'Clear all';
    btnNone.style.marginRight = '12px';
    btnNone.onclick = function(e) {
        e.preventDefault();
        toggleables.forEach(function(entry) {
            Plotly.restyle(gd, {'visible': 'legendonly'}, entry.indices);
            entry.checkbox.checked = false;
        });
    };

    ctrl.appendChild(btnAll);
    ctrl.appendChild(btnNone);

    // helper to create a checkbox + label
    function mkCheckbox(id, label, checked, onchange) {
        var wrap = document.createElement('label');
        wrap.style.marginRight = '12px';
        wrap.style.display = 'inline-flex';
        wrap.style.alignItems = 'center';

        var cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.id = id;
        cb.checked = checked;
        cb.style.marginRight = '6px';
        cb.addEventListener('change', onchange);

        var txt = document.createTextNode(label);
        wrap.appendChild(cb);
        wrap.appendChild(txt);
        return {wrap: wrap, checkbox: cb};
    }

    // Build groups from meta.component if present; otherwise fall back to name-based grouping
    var groups = {};
    for (var i = 0; i < gd.data.length; i++) {
        var tr = gd.data[i];
        var key = (tr && tr.meta && tr.meta.component) ? tr.meta.component : null;
        if (!key) {
            if (tr && typeof tr.name === 'string' && /daily\s*return/i.test(tr.name)) {
                key = 'dailyr_unknown';
            } else {
                key = 'trace_by_index';
            }
        }
        if (!groups[key]) groups[key] = {indices: [], sampleName: (tr && tr.name) || null};
        groups[key].indices.push(i);
    }

    var totalTraces = gd.data.length;

    if (groups['segments']) {
        var segIndices = groups['segments'].indices;
        var segLabel = 'Segments (' + segIndices.length + ')';
        var segDefaultChecked = (gd.data[segIndices[0]].visible !== 'legendonly' && gd.data[segIndices[0]].visible !== false);
        var segEntry = mkCheckbox(plot_id + '-segments', segLabel, segDefaultChecked, function() {
            var vis = this.checked ? true : false;
            Plotly.restyle(gd, {'visible': vis}, segIndices);
        });
        ctrl.appendChild(segEntry.wrap);
        toggleables.push({id: plot_id + '-segments', checkbox: segEntry.checkbox, indices: segIndices});
    }

    if (groups['hover']) {
        var hovIdx = groups['hover'].indices;
        var hovDefaultChecked = (gd.data[hovIdx[0]].visible !== 'legendonly' && gd.data[hovIdx[0]].visible !== false);
        var hovEntry = mkCheckbox(plot_id + '-hover', 'Hover overlay', hovDefaultChecked, function() {
            var vis = this.checked ? true : false;
            Plotly.restyle(gd, {'visible': vis}, hovIdx);
        });
        ctrl.appendChild(hovEntry.wrap);
        toggleables.push({id: plot_id + '-hover', checkbox: hovEntry.checkbox, indices: hovIdx});
    }

    Object.keys(groups).forEach(function(k) {
        if (k === 'segments' || k === 'hover') return;
        var idxs = groups[k].indices;
        if (idxs.length === 0) return;
        if (idxs.length === 1 && totalTraces <= MAX_CHECKBOXES) {
            var i = idxs[0];
            var tr = gd.data[i];
            var name = tr && tr.name ? tr.name : 'trace ' + i;
            var defaultChecked = (tr.visible !== 'legendonly' && tr.visible !== false);
            var entry = mkCheckbox(plot_id + '-cb-' + i, name, defaultChecked, function() {
                var vis = this.checked ? true : 'legendonly';
                Plotly.restyle(gd, {'visible': vis}, [i]);
            });
            ctrl.appendChild(entry.wrap);
            toggleables.push({id: plot_id + '-cb-' + i, checkbox: entry.checkbox, indices: [i]});
        } else if (idxs.length <= 6 && totalTraces <= MAX_CHECKBOXES) {
            idxs.forEach(function(i) {
                var tr = gd.data[i];
                var name = tr && tr.name ? tr.name : 'trace ' + i;
                var defaultChecked = (tr.visible !== 'legendonly' && tr.visible !== false);
                var entry = mkCheckbox(plot_id + '-cb-' + i, name, defaultChecked, function() {
                    var vis = this.checked ? true : 'legendonly';
                    Plotly.restyle(gd, {'visible': vis}, [i]);
                });
                ctrl.appendChild(entry.wrap);
                toggleables.push({id: plot_id + '-cb-' + i, checkbox: entry.checkbox, indices: [i]});
            });
        } else {
            var label = (groups[k].sampleName ? groups[k].sampleName : k) + ' (' + idxs.length + ')';
            var defaultChecked = (gd.data[idxs[0]].visible !== 'legendonly' && gd.data[idxs[0]].visible !== false);
            var gEntry = mkCheckbox(plot_id + '-group-' + k, label, defaultChecked, function() {
                var vis = this.checked ? true : false;
                Plotly.restyle(gd, {'visible': vis}, idxs);
            });
            ctrl.appendChild(gEntry.wrap);
            toggleables.push({id: plot_id + '-group-' + k, checkbox: gEntry.checkbox, indices: idxs});
        }
    });

    var hasShapes = (gd._orig_shapes && gd._orig_shapes.length > 0) || (gd._orig_annos && gd._orig_annos.length > 0);
    if (hasShapes) {
        var maxDefault = true;
        var maxEntry = mkCheckbox(plot_id + '-maxprofit', 'Max Profit', maxDefault, function() {
            if (this.checked) {
                Plotly.relayout(gd, {shapes: gd._orig_shapes, annotations: gd._orig_annos});
            } else {
                Plotly.relayout(gd, {shapes: [], annotations: []});
            }
        });
        ctrl.appendChild(maxEntry.wrap);
    }

    gd.parentNode.insertBefore(ctrl, gd);
}
