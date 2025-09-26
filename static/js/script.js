$(document).ready(function () {
    // state
    let currentSymbol = (window.__INITIAL_SYMBOL__ || 'AAPL').toUpperCase();
    let currentPeriod = (window.__INITIAL_PERIOD__ || '6mo');
    let comparePeriod = '6mo';
    let compareSymbol1 = '';
    let compareSymbol2 = '';
    let mpPeriod = '6mo';

    // ---------- Helpers ----------
    function showSpinner(id, show) {
        $(id)[show ? 'show' : 'hide']();
    }
    function showError(id, text) {
        if (text) { $(id).text(text).show(); } else { $(id).hide().text(''); }
    }
    function plotInto(divId, figObj) {
        // figObj is the parsed result of fig.to_json() => {data:[], layout:{}}
        Plotly.newPlot(divId, figObj.data, figObj.layout, {responsive: true});
    }
    function populateAutocomplete(inputSelector, resultsSelector, data) {
        const inputVal = $(inputSelector).val().trim().toUpperCase();
        const results = $(resultsSelector);
        results.empty();
        if (data.length > 0) {
            const filtered = data.filter(s => s.toUpperCase() !== inputVal);
            filtered.forEach(s => results.append(`<div class="autocomplete-item" data-symbol="${s}">${s}</div>`));
            filtered.length ? results.show() : results.hide();
        } else {
            results.hide();
        }
    }

    // Close autocomplete when clicking outside
    $(document).on('click', function (e) {
        if (!$(e.target).closest('.search-container').length) {
            $('.autocomplete-results').hide();
        }
    });

    // ---------- Single Stock ----------
    function loadStockData(symbol, period) {
        showSpinner('#loadingSpinner', true);
        $('#stockInfo').hide();
        showError('#chartError', '');
        $.getJSON('/get_stock_data', { symbol, period }, function (data) {
            showSpinner('#loadingSpinner', false);
            if (data.error) {
                showError('#chartError', data.error);
                return;
            }
            currentSymbol = data.symbol;
            $('#companyName').text(data.companyName);
            $('#stockSymbol').text(data.symbol);
            $('#stockPrice').text('$' + data.currentPrice.toFixed(2));

            const changeElem = $('#stockChange');
            changeElem.text((data.change >= 0 ? '+' : '') + data.change.toFixed(2) +
                ' (' + (data.changePercent >= 0 ? '+' : '') + data.changePercent.toFixed(2) + '%)');
            changeElem.removeClass('positive-change negative-change');
            changeElem.addClass(data.change >= 0 ? 'positive-change badge' : 'negative-change badge');

            $('#stockInfo').show();
            loadStockChart(symbol, period);
        }).fail(function () {
            showSpinner('#loadingSpinner', false);
            showError('#chartError', 'Error fetching stock data');
        });
    }

    function loadStockChart(symbol, period) {
        $.getJSON('/get_stock_chart', { symbol, period }, function (res) {
            if (res.error) {
                showError('#chartError', res.error);
                return;
            }
            plotInto('stockChart', res.fig);
        }).fail(function () {
            showError('#chartError', 'Error loading chart');
        });
    }

    // Search input (single)
    $('#stockSearch').on('input', function () {
        const q = $(this).val().trim();
        if (!q) return $('#autocompleteResults').hide();
        $.getJSON('/search_stocks', { q }, function (data) {
            populateAutocomplete('#stockSearch', '#autocompleteResults', data);
        });
    });
    $(document).on('click', '#autocompleteResults .autocomplete-item', function () {
        const symbol = $(this).data('symbol');
        $('#stockSearch').val(symbol);
        $('#autocompleteResults').hide();
        loadStockData(symbol, currentPeriod);
    });
    $('#searchBtn').on('click', function () {
        const symbol = $('#stockSearch').val().trim().toUpperCase();
        if (symbol) loadStockData(symbol, currentPeriod);
    });

    // Period (single)
    $(document).on('click', '.period-btn', function () {
        $('.period-btn').removeClass('active'); $(this).addClass('active');
        currentPeriod = $(this).data('period');
        if (currentSymbol) loadStockData(currentSymbol, currentPeriod);
    });

    // ---------- Compare ----------
    $('#compareStock1, #compareStock2').on('input', function () {
        const inputId = $(this).attr('id');
        const resultsId = inputId === 'compareStock1' ? '#autocompleteResults1' : '#autocompleteResults2';
        const q = $(this).val().trim();
        if (!q) return $(resultsId).hide();
        $.getJSON('/search_stocks', { q }, function (data) {
            const el = $(resultsId);
            el.empty();
            data.forEach(s => el.append(`<div class="autocomplete-item" data-input="${inputId}" data-symbol="${s}">${s}</div>`));
            data.length ? el.show() : el.hide();
        });
    });

    $(document).on('click', '#autocompleteResults1 .autocomplete-item, #autocompleteResults2 .autocomplete-item', function () {
        const inputId = $(this).data('input');
        const symbol = $(this).data('symbol');
        $('#' + inputId).val(symbol);
        if (inputId === 'compareStock1') {
            compareSymbol1 = symbol;
            updateCompareStockInfo(symbol, 1);
            $('#autocompleteResults1').hide();
        } else {
            compareSymbol2 = symbol;
            updateCompareStockInfo(symbol, 2);
            $('#autocompleteResults2').hide();
        }
    });

    function updateCompareStockInfo(symbol, n) {
        $.getJSON('/get_stock_data', { symbol, period: comparePeriod }, function (d) {
            if (d.error) return;
            $(`#compareCompanyName${n}`).text(d.companyName);
            $(`#compareStockSymbol${n}`).text(d.symbol);
            $(`#compareStockPrice${n}`).text('$' + d.currentPrice.toFixed(2));
            const ch = $(`#compareStockChange${n}`);
            ch.text((d.change >= 0 ? '+' : '') + d.change.toFixed(2) + ' (' + (d.changePercent >= 0 ? '+' : '') + d.changePercent.toFixed(2) + '%)');
            ch.removeClass('positive-change negative-change').addClass(d.change >= 0 ? 'positive-change badge' : 'negative-change badge');
            $(`#compareStockInfo${n}`).show();
        });
    }

    function compareStocks(symbol1, symbol2, period) {
        showSpinner('#compareLoadingSpinner', true);
        showError('#compareChartError', '');
        $.getJSON('/compare_stocks', { symbol1, symbol2, period }, function (res) {
            showSpinner('#compareLoadingSpinner', false);
            if (res.error) {
                showError('#compareChartError', res.error);
                return;
            }
            // update headers
            $('#compareCompanyName1').text(res.companyName1);
            $('#compareStockSymbol1').text(res.symbol1);
            $('#compareStockPrice1').text('$' + res.currentPrice1.toFixed(2));
            const c1 = $('#compareStockChange1');
            c1.text((res.change1 >= 0 ? '+' : '') + res.change1.toFixed(2) + ' (' + (res.changePercent1 >= 0 ? '+' : '') + res.changePercent1.toFixed(2) + '%)');
            c1.removeClass('positive-change negative-change').addClass(res.change1 >= 0 ? 'positive-change badge' : 'negative-change badge');
            $('#compareStockInfo1').show();

            $('#compareCompanyName2').text(res.companyName2);
            $('#compareStockSymbol2').text(res.symbol2);
            $('#compareStockPrice2').text('$' + res.currentPrice2.toFixed(2));
            const c2 = $('#compareStockChange2');
            c2.text((res.change2 >= 0 ? '+' : '') + res.change2.toFixed(2) + ' (' + (res.changePercent2 >= 0 ? '+' : '') + res.changePercent2.toFixed(2) + '%)');
            c2.removeClass('positive-change negative-change').addClass(res.change2 >= 0 ? 'positive-change badge' : 'negative-change badge');
            $('#compareStockInfo2').show();

            plotInto('compareChart', res.fig);
        }).fail(function () {
            showSpinner('#compareLoadingSpinner', false);
            showError('#compareChartError', 'Error comparing stocks');
        });
    }

    $('#compareBtn').on('click', function () {
        const s1 = $('#compareStock1').val().trim().toUpperCase();
        const s2 = $('#compareStock2').val().trim().toUpperCase();
        if (s1 && s2) compareStocks(s1, s2, comparePeriod);
        else showError('#compareChartError', 'Please select two stocks to compare');
    });

    $(document).on('click', '.compare-period-btn', function () {
        $('.compare-period-btn').removeClass('active'); $(this).addClass('active');
        comparePeriod = $(this).data('period');
        const s1 = $('#compareStock1').val().trim().toUpperCase();
        const s2 = $('#compareStock2').val().trim().toUpperCase();
        if (s1 && s2) compareStocks(s1, s2, comparePeriod);
    });

    // ---------- Max Profit ----------
    function loadMaxProfit(symbol, period) {
        showSpinner('#maxProfitSpinner', true);
        showError('#maxProfitError', '');
        $('#maxProfitInfo').hide().text('');
        $.getJSON('/max_profit', { symbol, period }, function (res) {
            showSpinner('#maxProfitSpinner', false);
            if (res.error) {
                showError('#maxProfitError', res.error);
                return;
            }
            plotInto('maxProfitChart', res.fig);
            $('#maxProfitInfo').html(
                `Best window — <strong>Buy</strong> ${res.buyDate} @ $${res.buyPrice} &nbsp;→&nbsp; <strong>Sell</strong> ${res.sellDate} @ $${res.sellPrice} &nbsp;(<strong>Profit</strong>: $${res.profit})`
            ).show();
        }).fail(function () {
            showSpinner('#maxProfitSpinner', false);
            showError('#maxProfitError', 'Error finding max profit window');
        });
    }

    $('#maxProfitBtn').on('click', function () {
        const symbol = $('#maxProfitStock').val().trim().toUpperCase() || currentSymbol;
        if (symbol) loadMaxProfit(symbol, mpPeriod);
    });

    $(document).on('click', '.mp-period-btn', function () {
        $('.mp-period-btn').removeClass('active'); $(this).addClass('active');
        mpPeriod = $(this).data('period');
        const symbol = $('#maxProfitStock').val().trim().toUpperCase() || currentSymbol;
        if (symbol) loadMaxProfit(symbol, mpPeriod);
    });

    // autocomplete for max profit
    $('#maxProfitStock').on('input', function () {
        const q = $(this).val().trim();
        if (!q) return $('#autocompleteResultsMax').hide();
        $.getJSON('/search_stocks', { q }, function (data) {
            const el = $('#autocompleteResultsMax'); el.empty();
            data.forEach(s => el.append(`<div class="autocomplete-item" data-target="#maxProfitStock" data-symbol="${s}">${s}</div>`));
            data.length ? el.show() : el.hide();
        });
    });

    // ---------- Daily Returns ----------
    function fetchDailyReturns(symbol, period) {
        showSpinner('#drLoadingSpinner', true);
        $('#dailyReturnTableContainer').hide();
        showError('#drChartError', '');
        $.getJSON('/daily_returns', { symbol, period }, function (data) {
            showSpinner('#drLoadingSpinner', false);
            if (data.error) {
                showError('#drChartError', data.error);
                return;
            }
            plotInto('dailyReturnChart', data.fig);
            const tbody = $('#dailyReturnTableBody');
            tbody.empty();
            data.table.forEach(r => {
                tbody.append(`
                    <tr>
                      <td>${r.Date}</td>
                      <td>${r["Adj Close"].toFixed ? r["Adj Close"].toFixed(2) : r["Adj Close"]}</td>
                      <td>${r["Daily Return"].toFixed ? r["Daily Return"].toFixed(2) : r["Daily Return"]}%</td>
                    </tr>
                `);
            });
            $('#dailyReturnTableContainer').show();
        }).fail(function () {
            showSpinner('#drLoadingSpinner', false);
            showError('#drChartError', 'Error fetching daily returns');
        });
    }

    // daily returns search + autocomplete
    $('#dailyReturnStock').on('input', function () {
        const q = $(this).val().trim();
        if (!q) return $('#dailyReturnAutocompleteResults').hide();
        $.getJSON('/search_stocks', { q }, function (data) {
            populateAutocomplete('#dailyReturnStock', '#dailyReturnAutocompleteResults', data);
        });
    });

    $(document).on('click', '#dailyReturnAutocompleteResults .autocomplete-item', function () {
        const symbol = $(this).data('symbol');
        $('#dailyReturnStock').val(symbol);
        $('#dailyReturnAutocompleteResults').hide();
        fetchDailyReturns(symbol, $('.dr-period-btn.active').data('period') || '6mo');
    });

    $('#dailyReturnBtn').on('click', function () {
        const symbol = $('#dailyReturnStock').val().trim().toUpperCase();
        if (symbol) fetchDailyReturns(symbol, $('.dr-period-btn.active').data('period') || '6mo');
    });

    $(document).on('click', '.dr-period-btn', function () {
        $('.dr-period-btn').removeClass('active'); $(this).addClass('active');
        const symbol = $('#dailyReturnStock').val().trim().toUpperCase();
        if (symbol) fetchDailyReturns(symbol, $(this).data('period'));
    });

    // ---------- Popular stocks ----------
    $(document).on('click', '.stock-btn', function () {
        const symbol = $(this).data('symbol');
        const activeTabId = $('.nav-link.active').attr('id');
        if (activeTabId === 'single-tab') {
            $('#stockSearch').val(symbol);
            loadStockData(symbol, currentPeriod);
        } else if (activeTabId === 'compare-tab') {
            if (!compareSymbol1) {
                $('#compareStock1').val(symbol);
                compareSymbol1 = symbol;
                updateCompareStockInfo(symbol, 1);
            } else if (!compareSymbol2) {
                $('#compareStock2').val(symbol);
                compareSymbol2 = symbol;
                updateCompareStockInfo(symbol, 2);
            } else {
                $('#compareStock1').val(symbol);
                compareSymbol1 = symbol;
                updateCompareStockInfo(symbol, 1);
            }
        } else if (activeTabId === 'maxprofit-tab') {
            $('#maxProfitStock').val(symbol);
            loadMaxProfit(symbol, mpPeriod);
        } else if (activeTabId === 'dailyreturns-tab') {
            $('#dailyReturnStock').val(symbol);
            fetchDailyReturns(symbol, $('.dr-period-btn.active').data('period') || '6mo');
        }
    });

    // ---------- Shared autocomplete click (max profit generic handler) ----------
    $(document).on('click', '.autocomplete-item[data-target]', function () {
        const target = $(this).data('target');
        const symbol = $(this).data('symbol');
        $(target).val(symbol);
        $(this).closest('.autocomplete-results').hide();
    });

    // Reset compare tab when switching back to single (kept from your original behavior)
    $('button[data-bs-toggle="tab"]').on('shown.bs.tab', function (e) {
        if (e.target.id === 'single-tab') {
            $('#compareStock1').val('');
            $('#compareStock2').val('');
            $('#compareStockInfo1, #compareStockInfo2').hide();
            compareSymbol1 = '';
            compareSymbol2 = '';
            // keep chart as-is; it updates when user interacts
        }
    });

    // ---------- Initial load ----------
    // activate period button based on initial period if present
    $('.period-btn').removeClass('active');
    $(`.period-btn[data-period="${currentPeriod}"]`).addClass('active');
    loadStockData(currentSymbol, currentPeriod);
});
