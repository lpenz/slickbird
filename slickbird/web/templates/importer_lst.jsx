
var ImporterfileRow = React.createClass({
    render: function() {
        var c = this.props.c;
        return (
            <tr><td>{c.filename}</td><td>{c.status}</td></tr>
        );
    },
});

var ImporterfileTop = React.createClass({
    getInitialState: function() {
        return {data: []};
    },
    loadData: function() {
        $.ajax({
            url: this.props.url,
            dataType: 'json',
            cache: false,
            success: function(data) {
                this.setState({data: data});
            }.bind(this),
            error: function(xhr, status, err) {
                console.error(this.props.url, status, err.toString());
            }.bind(this)
        });
    },
    componentDidMount: function() {
        this.loadData();
        setInterval(this.loadData, 2000);
    },
    render: function() {
        var importerfileRows = this.state.data.map(function (c) {
            return (
                <ImporterfileRow key={c.id} c={c}/>
            );
        });
        return (
            <table className="table">
                <tbody>
                    <tr><th>File</th><th>Status</th></tr>
                    {importerfileRows}
                </tbody>
            </table>
        );
    }
});

React.render(
    <ImporterfileTop url="{{ reverse_url("api_importer_lst") }}" />,
        document.getElementById('importer')
);

