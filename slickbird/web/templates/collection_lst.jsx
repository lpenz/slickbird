
var CollectionRow = React.createClass({
    render: function() {
        var c = this.props.c;
        var url = "{{ reverse_url("game_lst", "placeholder") }}".replace("placeholder", c.name)
        return (
            <tr>
                <td><a href={url}>{c.name}</a></td>
                <td>{c.status}</td>
            </tr>
        );
    }
});

var CollectionTable = React.createClass({
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
        var collectionRows = this.state.data.map(function (c) {
            return (
                <CollectionRow key={c.id} c={c}/>
            );
        });
        return (
            <table className="table">
                <tbody>
                    <tr><th>Collection</th><th>Status</th></tr>
                    {collectionRows}
                </tbody>
            </table>
        );
    }
});

React.render(
  <CollectionTable url="{{ reverse_url("api_collection_lst") }}" />,
  document.getElementById('collection')
);

