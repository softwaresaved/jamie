d3.json('by_year.json', function(data) {
    MG.data_graphic({
        title: "Number of jobs by year",
        data: data,
        width: 450,
        height: 250,
        area: false,
        color: "#2155a8",
        target: '#njobsyear',
        x_accessor: 'group',
        y_accessor: 'npos',
        show_confidence_band: ['npos_lower', 'npos_upper'],
        brush: 'x'
    })
})
d3.json('by_year.json', function(data) {
    MG.data_graphic({
        title: "Proportion of jobs by year",
        data: data,
        width: 450,
        height: 250,
        area: false,
        color: "#2155a8",
        target: '#propjobsyear',
        x_accessor: 'group',
        y_accessor: 'proportion_pos',
        brush: 'x'
    })
})
d3.json('by_month.json', function(data) {
    data = MG.convert.date(data, 'group');
    MG.data_graphic({
        title: "Number of jobs by month",
        data: data,
        width: 450,
        height: 250,
        area: false,
        color: "#2155a8",
        target: '#njobsmonth',
        x_accessor: 'group',
        y_accessor: 'npos',
        show_confidence_band: ['npos_lower', 'npos_upper'],
        brush: 'x'
    })
})
d3.json('by_month.json', function(data) {
    data = MG.convert.date(data, 'group');
    MG.data_graphic({
        title: "Proportion of jobs by month",
        data: data,
        width: 450,
        height: 250,
        area: false,
        color: "#2155a8",
        target: '#propjobsmonth',
        x_accessor: 'group',
        y_accessor: 'proportion_pos',
        brush: 'x'
    })
})
d3.json('by_year.json', function(data) {
    MG.data_graphic({
        title: "Mean salary",
        data: data,
        width: 450,
        height: 250,
        area: false,
        color: "#2155a8",
        target: '#meansalary',
        x_accessor: 'group',
        y_accessor: 'salary_mean_pos',
        brush: 'x'
    })
})
d3.json('by_year.json', function(data) {
    MG.data_graphic({
        title: "Number of jobs matching target job title",
        data: data,
        width: 450,
        height: 250,
        area: false,
        color: "#2155a8",
        target: '#njobsmatch',
        x_accessor: 'group',
        y_accessor: 'njob_match',
        brush: 'x'
    })
})
d3.json('by_year.json', function(data) {
    MG.data_graphic({
        title: "Number of jobs per year by contract type",
        data: data,
        width: 450,
        height: 250,
        area: false,
        color: "#2155a8",
        target: '#ncontract',
        x_accessor: 'group',
        y_accessor: ['ncontract_permanent', 'ncontract_fixed_term'],
        legend: ['Permanent', 'Fixed Term'],
        brush: 'x'
    })
})
d3.json('by_year.json', function(data) {
    MG.data_graphic({
        title: "Proportion of jobs per year by contract type",
        data: data,
        width: 450,
        height: 250,
        area: false,
        color: "#2155a8",
        target: '#propcontract',
        x_accessor: 'group',
        y_accessor: ['propcontract_permanent', 'propcontract_fixed_term'],
        legend: ['Permanent', 'Fixed Term'],
        brush: 'x'
    })
})
d3.json('by_year.json', function(data) {
    MG.data_graphic({
        title: "Job locations",
        data: data,
        width: 950,
        height: 300,
        area: false,
        color: "#2155a8",
        target: '#location',
        x_accessor: 'group',
        legend_target: '.legend',
        y_accessor: [
            "nloc_africa",
            "nloc_all_locations",
            "nloc_asia_middle_east",
            "nloc_north_south_central_america",
            "nloc_europe",
            "nloc_republic_of_ireland",
            "nloc_london",
            "nloc_northern_england",
            "nloc_midlands_of_england",
            "nloc_south_east_england",
            "nloc_south_west_england",
            "nloc_northern_ireland",
            "nloc_scotland",
            "nloc_wales",
        ],
        legend: [
            "Africa",
            "All Locations",
            "Asia & Middle East",
            "Americas",
            "Europe",
            "Republic of Ireland",
            "London",
            "Northern England",
            "Midlands England",
            "South East England",
            "South West England",
            "Northern Ireland",
            "Scotland",
            "Wales"
        ],
        brush: 'x'
    })
})

d3.json('training_by_month.json', function(data) {
    data = MG.convert.date(data, 'group');
    MG.data_graphic({
        title: "Total number of jobs by month",
        data: data,
        width: 450,
        height: 250,
        area: false,
        color: "#2155a8",
        target: '#trainjobs',
        x_accessor: 'group',
        y_accessor: 'total',
        brush: 'x'
    })
})
d3.json('training_by_month.json', function(data) {
    data = MG.convert.date(data, 'group');
    MG.data_graphic({
        title: "Proportion of target job type by month",
        data: data,
        width: 450,
        height: 250,
        area: false,
        color: "#2155a8",
        target: '#trainpropjobs',
        x_accessor: 'group',
        y_accessor: 'proportion_pos',
        brush: 'x'
    })
})

