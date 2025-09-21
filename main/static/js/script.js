$(document).ready(function() {
    let currentSymbol = '';
    let currentPeriod = '6mo';
    let comparePeriod = '6mo';
    let compareSymbol1 = '';
    let compareSymbol2 = '';

    function populateAutocomplete(inputSelector, resultsSelector, data) {
        const inputVal = $(inputSelector).val().trim().toUpperCase();
        const results = $(resultsSelector);
        results.empty();

        if (data.length > 0) {
            // Filter out exact match to avoid showing the typed input as an option
            const filteredData = data.filter(stock => stock.toUpperCase() !== inputVal);

            filteredData.forEach(function(stock) {
                results.append('<div class="autocomplete-item" data-symbol="' + stock + '">' + stock + '</div>');
            });

            if (filteredData.length > 0) {
                results.show();
            } else {
                results.hide();
            }
        } else {
            results.hide();
        }  
    }
    // ============================
    // Single Stock Feature
    // ============================
    loadStockData('AAPL', currentPeriod);

    $('#stockSearch').on('input', function() {
        const query = $(this).val().trim();
        if (query.length < 1) {
            $('#autocompleteResults').hide();
            return;
        }

        $.getJSON('/search_stocks', { q: query }, function(data) {
            const results = $('#autocompleteResults');
            results.empty();
            if (data.length > 0) {
                data.forEach(stock => {
                    results.append(`<div class="autocomplete-item" data-symbol="${stock}">${stock}</div>`);
                });
                results.show();
            } else {
                results.hide();
            }
        });
    });

    $(document).on('click', '#autocompleteResults .autocomplete-item', function() {
        const symbol = $(this).data('symbol');
        $('#stockSearch').val(symbol);
        $('#autocompleteResults').hide();
        loadStockData(symbol, currentPeriod);
    });

    $('#searchBtn').click(function() {
        const symbol = $('#stockSearch').val().trim().toUpperCase();
        if (symbol) loadStockData(symbol, currentPeriod);
    });

    // ============================
    // Compare Stocks Feature
    // ============================
    $('#compareStock1, #compareStock2').on('input', function() {
        const inputId = $(this).attr('id');
        const resultsId = inputId === 'compareStock1' ? 'autocompleteResults1' : 'autocompleteResults2';
        const query = $(this).val().trim();

        if (query.length < 1) {
            $('#' + resultsId).hide();
            return;
        }

        $.getJSON('/search_stocks', { q: query }, function(data) {
            const results = $('#' + resultsId);
            results.empty();
            if (data.length > 0) {
                data.forEach(stock => {
                    results.append(`<div class="autocomplete-item" data-symbol="${stock}" data-input="${inputId}">${stock}</div>`);
                });
                results.show();
            } else {
                results.hide();
            }
        });
    });

    $(document).on('click', '.autocomplete-item', function() {
        const symbol = $(this).data('symbol');
        const inputId = $(this).data('input');

        if (inputId) {
            $('#' + inputId).val(symbol);
            $('#' + (inputId === 'compareStock1' ? 'autocompleteResults1' : 'autocompleteResults2')).hide();

            if (inputId === 'compareStock1') {
                compareSymbol1 = symbol;
                updateCompareStockInfo(symbol, 1);
            } else {
                compareSymbol2 = symbol;
                updateCompareStockInfo(symbol, 2);
            }
        } else {
            $('#stockSearch').val(symbol);
            $('#autocompleteResults').hide();
            loadStockData(symbol, currentPeriod);
        }
    });

    $('#compareBtn').click(function() {
        const symbol1 = $('#compareStock1').val().trim().toUpperCase();
        const symbol2 = $('#compareStock2').val().trim().toUpperCase();
        if (symbol1 && symbol2) {
            compareStocks(symbol1, symbol2, comparePeriod);
        } else {
            $('#compareChartError').text('Please select two stocks to compare').show();
        }
    });

    $(document).on('click', '.stock-btn', function() {
        const symbol = $(this).data('symbol');
        const activeTab = $('.nav-link.active').attr('id');

        if (activeTab === 'single-tab') {
            $('#stockSearch').val(symbol);
            loadStockData(symbol, currentPeriod);
        } else if (activeTab === 'compare-tab') {
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
        }
    });

    $(document).on('click', function(e) {
        if (!$(e.target).closest('.search-container').length) {
            $('.autocomplete-results').hide();
        }
    });

    // Period buttons
    $(document).on('click', '.period-btn', function() {
        $('.period-btn').removeClass('active');
        $(this).addClass('active');
        currentPeriod = $(this).data('period');
        if (currentSymbol) loadStockData(currentSymbol, currentPeriod);
    });

    $(document).on('click', '.compare-period-btn', function() {
        $('.compare-period-btn').removeClass('active');
        $(this).addClass('active');
        comparePeriod = $(this).data('period');
        if (compareSymbol1 && compareSymbol2) compareStocks(compareSymbol1, compareSymbol2, comparePeriod);
    });

    $('button[data-bs-toggle="tab"]').on('shown.bs.tab', function(e) {
        if (e.target.id === 'single-tab') {
            $('#compareStock1').val('');
            $('#compareStock2').val('');
            $('#compareStockInfo1').hide();
            $('#compareStockInfo2').hide();
            $('#compareChart').hide();
            compareSymbol1 = '';
            compareSymbol2 = '';
        }
    });

    // ============================
    // Daily Returns Feature
    // ============================
    let drSelectedIndex = -1;
    let drPeriod = '6mo';

    $('.dr-period-btn').click(function() {
        $('.dr-period-btn').removeClass('active');
        $(this).addClass('active');
        drPeriod = $(this).data('period');

        const symbol = $('#dailyReturnStock').val().trim().toUpperCase();
        if (symbol) fetchDailyReturns(symbol, drPeriod);
    });

    $('#dailyReturnStock').on('input', function() {
        const query = $(this).val().trim();
        drSelectedIndex = -1;

        if (query.length < 1) {
            $('#dailyReturnAutocompleteResults').hide();
            return;
        }

        $.getJSON('/search_stocks', { q: query }, function(data) {
            const results = $('#dailyReturnAutocompleteResults');
            results.empty();
            if (data.length > 0) {
                data.forEach(stock => {
                    results.append(`<div class="autocomplete-item" data-symbol="${stock}">${stock}</div>`);
                });
                results.show();
            } else {
                results.hide();
            }
        });
    });

    $(document).on('click', '#dailyReturnAutocompleteResults .autocomplete-item', function() {
        const symbol = $(this).data('symbol');
        selectDailyReturnSymbol(symbol);
    });

    $('#dailyReturnStock').on('keydown', function(e) {
        const items = $('#dailyReturnAutocompleteResults .autocomplete-item');
        if (!items.length) return;

        if (e.key === 'ArrowDown') {
            drSelectedIndex = (drSelectedIndex + 1) % items.length;
            highlightDRItem(items, drSelectedIndex);
            e.preventDefault();
        } else if (e.key === 'ArrowUp') {
            drSelectedIndex = (drSelectedIndex - 1 + items.length) % items.length;
            highlightDRItem(items, drSelectedIndex);
            e.preventDefault();
        } else if (e.key === 'Enter') {
            if (drSelectedIndex >= 0 && drSelectedIndex < items.length) {
                selectDailyReturnSymbol($(items[drSelectedIndex]).data('symbol'));
                e.preventDefault();
            }
        }
    });

    function highlightDRItem(items, index) {
        items.removeClass('active');
        $(items[index]).addClass('active');
    }

    function selectDailyReturnSymbol(symbol) {
        $('#dailyReturnStock').val(symbol);
        $('#dailyReturnAutocompleteResults').hide();
        fetchDailyReturns(symbol, drPeriod);
    }

    $("#dailyReturnBtn").click(function() {
        const symbol = $("#dailyReturnStock").val().trim().toUpperCase();
        if (symbol) fetchDailyReturns(symbol, drPeriod);
    });

    function fetchDailyReturns(symbol, period) {
        $("#drLoadingSpinner").show();
        $("#drChartError").hide();
        $("#dailyReturnChart").hide();
        $("#dailyReturnTableContainer").hide();

        $.getJSON(`/daily_returns?symbol=${symbol}&period=${period}`, function(data) {
            $("#drLoadingSpinner").hide();

            if (data.error) {
                $("#drChartError").text(data.error).show();
                return;
            }

            $("#dailyReturnChart").attr("src", "data:image/png;base64," + data.chart).show();

            const tbody = $("#dailyReturnTableBody");
            tbody.empty();
            data.table.forEach(row => {
                tbody.append(`
                    <tr>
                        <td>${row.Date}</td>
                        <td>${row["Adj Close"]}</td>
                        <td>${row["Daily Return"]}%</td>
                    </tr>
                `);
            });
            $("#dailyReturnTableContainer").show();
        }).fail(function() {
            $("#drLoadingSpinner").hide();
            $("#drChartError").text("Error fetching daily returns").show();
        });
    }

    $(document).on('click', function(e) {
        if (!$(e.target).closest('#dailyReturnStock, #dailyReturnAutocompleteResults').length) {
            $('#dailyReturnAutocompleteResults').hide();
        }
    });

    // ============================
    // Functions to fetch stock data / charts
    // ============================
    function loadStockData(symbol, period) {
        $('#loadingSpinner').show();
        $('#stockChart').hide();
        $('#chartError').hide();

        $.getJSON('/get_stock_data', { symbol, period }, function(data) {
            $('#loadingSpinner').hide();
            if (data.error) {
                $('#chartError').text(data.error).show();
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
        }).fail(() => {
            $('#chartError').text('Error fetching stock data').show();
            $('#loadingSpinner').hide();
        });
    }

    function loadStockChart(symbol, period) {
        $.getJSON('/get_stock_chart', { symbol, period }, function(data) {
            $('#loadingSpinner').hide();
            if (data.error) {
                $('#chartError').text(data.error).show();
                return;
            }
            $('#stockChart').attr('src', 'data:image/png;base64,' + data.image).show();
        }).fail(() => {
            $('#loadingSpinner').hide();
            $('#chartError').text('Error loading chart').show();
        });
    }

    function updateCompareStockInfo(symbol, stockNum) {
        $.getJSON('/get_stock_data', { symbol, period: comparePeriod }, function(data) {
            if (data.error) return;

            $(`#compareCompanyName${stockNum}`).text(data.companyName);
            $(`#compareStockSymbol${stockNum}`).text(data.symbol);
            $(`#compareStockPrice${stockNum}`).text('$' + data.currentPrice.toFixed(2));

            const changeElem = $(`#compareStockChange${stockNum}`);
            changeElem.text((data.change >= 0 ? '+' : '') + data.change.toFixed(2) +
                ' (' + (data.changePercent >= 0 ? '+' : '') + data.changePercent.toFixed(2) + '%)');
            changeElem.removeClass('positive-change negative-change');
            changeElem.addClass(data.change >= 0 ? 'positive-change badge' : 'negative-change badge');

            $(`#compareStockInfo${stockNum}`).show();
        });
    }

    function compareStocks(symbol1, symbol2, period) {
        $('#compareLoadingSpinner').show();
        $('#compareChart').hide();
        $('#compareChartError').hide();

        $.getJSON('/compare_stocks', { symbol1, symbol2, period }, function(data) {
            $('#compareLoadingSpinner').hide();
            if (data.error) {
                $('#compareChartError').text(data.error).show();
                return;
            }

            $('#compareCompanyName1').text(data.companyName1);
            $('#compareStockSymbol1').text(data.symbol1);
            $('#compareStockPrice1').text('$' + data.currentPrice1.toFixed(2));
            const changeElem1 = $('#compareStockChange1');
            changeElem1.text((data.change1 >= 0 ? '+' : '') + data.change1.toFixed(2) +
                ' (' + (data.changePercent1 >= 0 ? '+' : '') + data.changePercent1.toFixed(2) + '%)');
            changeElem1.removeClass('positive-change negative-change');
            changeElem1.addClass(data.change1 >= 0 ? 'positive-change badge' : 'negative-change badge');

            $('#compareCompanyName2').text(data.companyName2);
            $('#compareStockSymbol2').text(data.symbol2);
            $('#compareStockPrice2').text('$' + data.currentPrice2.toFixed(2));
            const changeElem2 = $('#compareStockChange2');
            changeElem2.text((data.change2 >= 0 ? '+' : '') + data.change2.toFixed(2) +
                ' (' + (data.changePercent2 >= 0 ? '+' : '') + data.changePercent2.toFixed(2) + '%)');
            changeElem2.removeClass('positive-change negative-change');
            changeElem2.addClass(data.change2 >= 0 ? 'positive-change badge' : 'negative-change badge');

            $('#compareChart').attr('src', 'data:image/png;base64,' + data.image).show();
        }).fail(() => {
            $('#compareLoadingSpinner').hide();
            $('#compareChartError').text('Error comparing stocks').show();
        });
    }
    $('#dailyReturnStock').on('input', function() {
        const query = $(this).val().trim();
        if (!query) return $('#dailyReturnAutocompleteResults').hide();

        $.getJSON('/search_stocks', { q: query }, function(data) {
            populateAutocomplete('#dailyReturnStock', '#dailyReturnAutocompleteResults', data);
        });
    });
});