
var CollectionInfo = React.createClass({
    render: function() {
        return (
            <div className="panel panel-default">
                <div className="panel-body">
                    <h2>{this.props.c.name} <small>{this.props.c.status}</small></h2>
                </div>
                <button type="button" className="btn btn-primary" aria-pressed="false" onClick={this.props.gamelistReload} >
                    <span className="glyphicon glyphicon-repeat" aria-hidden="true"></span>
                </button>
                &nbsp;
                <button type="button" className="btn btn-primary" data-toggle="button" aria-pressed="false" onClick={this.props.hideMissingToggle} >
                    Hide missing
                </button>
            </div>
        )
    }
});

var GameRow = React.createClass({
    render: function() {
        var g = this.props.g;
        return (
            <tr>
                <td>{g.name}</td>
                <td>{g.nfo}</td>
                <td>{g.status}</td>
            </tr>
        )
    }
});

var CollectionTop = React.createClass({
    getInitialState: function() {
        return {
            hidemissing: false,
            data: {
                games: [],
                collection: {
                    name: this.props.collectionname,
                    status: '(loading)'
                }
            }
        };
    },
    loadData: function() {
        $.ajax({
            url: this.props.url+'?hidemissing='+this.state.hidemissing,
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
    gamelistReload: function() {
        $.post(this.props.url_reload);
    },
    hideMissingToggle: function() {
        this.setState({
            hidemissing: !this.state.hidemissing,
            data: this.state.data,
        });
        this.loadData();
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
                <CollectionInfo
                    key={c.name}
                    c={c}
                    hideMissingToggle={this.hideMissingToggle}
                    gamelistReload={this.gamelistReload}
                />
                <table className="table">
                    <tbody>
                        <tr>
                            <th>Game</th>
                            <th>NFO</th>
                            <th>Status</th>
                        </tr>
                        {gameRows}
                    </tbody>
                </table>
            </div>
        );
    }
});

