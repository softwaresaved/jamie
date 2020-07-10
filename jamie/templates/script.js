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

