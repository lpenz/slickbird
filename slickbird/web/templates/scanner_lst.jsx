
var ScannerfileRow = React.createClass({
    render: function() {
        var c = this.props.c;
        return (
            <tr><td>{c.filename}</td><td>{c.status}</td></tr>
        );
    },
});

var ScannerfileTop = React.createClass({
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
        var scannerfileRows = this.state.data.map(function (c) {
            return (
                <ScannerfileRow key={c.id} c={c}/>
            );
        });
        return (
            <table className="table">
                <tbody>
                    <tr><th>File</th><th>Status</th></tr>
                    {scannerfileRows}
                </tbody>
            </table>
        );
    }
});

React.render(
    <ScannerfileTop url="{{ reverse_url("api_scanner_lst") }}" />,
        document.getElementById('scanner')
);

