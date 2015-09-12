
var CollectionInfo = React.createClass({
    render: function() {
        return (
            <table className="table">
                <tbody>
                    <tr>
                    <th>{this.props.c.name}</th>
                    <td>{this.props.c.status}</td>
                    </tr>
                </tbody>
            </table>
        )
    }
});

var GameRow = React.createClass({
    render: function() {
        var g = this.props.g;
        return (
            <tr><td>{g.name}</td><td>{g.status}</td></tr>
        )
    }
});

var CollectionTop = React.createClass({
    getInitialState: function() {
        return {
            data: {
                games: [],
                collection: {
                    name: this.props.collectionname,
                    status: 'unknown'
                }
            }
        };
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
        var c = this.state.data.collection
        var gameRows = this.state.data.games.map(function (g) {
            return (
                <GameRow key={g.name} g={g} />
            );
        });
        return (
            <div>
                <CollectionInfo key={c.name} c={c} />
                <table className="table">
                    <tbody>
                        <tr><th>Game</th><th>Status</th></tr>
                        {gameRows}
                    </tbody>
                </table>
            </div>
        );
    }
});

