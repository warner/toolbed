
var yup = 1;

function fill(what, element) {
    $(element).text("updating...");
    $.ajax({type: "POST",
            url: "/control/api",
            contentType: "text/json", // what we send
            data: JSON.stringify({token: token, what: what}),
            // data: {a:foo,b:bar} makes .ajax to serialize like "a=foo&b=bar"
            dataType: 'json', // what we expect, and how to parse it
            success: function(data) { $(element).text(data.text); }
           });
};

$(function() {
      $("#tabs").tabs({selected: -1,
                       show: function(event, ui)
                       {
                           if (ui.index == 0) {
                               fill("webport", "#webport");
                               fill("relay_location", "#relay_location");
                               fill("pubkey", "#pubkey");
                           }
                           return true;
                       }
                       });
});
