
function fill(what, element) {
    $(element).text("updating...");
    $.ajax({type: "POST",
            url: "/relay/api",
            contentType: "text/json", // what we send
            data: JSON.stringify({what: what}),
            // data: {a:foo,b:bar} makes .ajax to serialize like "a=foo&b=bar"
            dataType: 'json', // what we expect, and how to parse it
            success: function(data) { $(element).text(data.text); }
           });
};

function fill_clients(what, element) {
    $(element).empty();
    $(element).append($("<li/>").text("updating.."));
    $.ajax({type: "POST",
            url: "/relay/api",
            contentType: "text/json", // what we send
            data: JSON.stringify({what: what}),
            dataType: 'json', // what we expect, and how to parse it
            success: function(data)
            {
                $(element).empty();
                for (var i=0; i <data.length; i++) {
                    var c = $("<li/>").text("client "+i);
                    $(element).append(c);
                    var c2 = $("<ul/>");
                    c.append(c2);
                    var cl = data[i];
                    c2.append($("<li/>").text("from: "+cl.from));
                    c2.append($("<li/>").text("since: "+cl.connected));
                    c2.append($("<li/>").text("messages received: "+cl.rx));
                    c2.append($("<li/>").text("messages sent: "+cl.tx));
                    c2.append($("<li/>").text("subscribing to: "+cl.subscriptions));
                };
            }
           });
};


$(function() {
      $("#tabs").tabs({selected: -1,
                       show: function(event, ui)
                       {
                           if (ui.index == 0) {
                               fill("webport", "#webport");
                               fill("relayport", "#relayport");
                           } else if (ui.index == 1) {
                               fill_clients("clients", "#clients");
                           }
                           return true;
                       }
                       });
});
