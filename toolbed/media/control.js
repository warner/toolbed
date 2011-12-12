
function doAPI(method, args, callback) {
    $.ajax({type: "POST",
            url: "/control/api",
            contentType: "text/json", // what we send
            data: JSON.stringify({token: token, method: method, args: args}),
            // data: {a:foo,b:bar} makes .ajax to serialize like "a=foo&b=bar"
            dataType: 'json', // what we expect, and how to parse it
            success: callback });
};

function fill(method, element) {
    $(element).text("updating...");
    doAPI(method, {}, function(data) { $(element).text(data.text); });
};

function sendMessage(event) {
    console.log("sendMessage");
    var args = {to: $("#message-to").val(),
                message: $("#message-message").val()
               };
    doAPI("sendMessage", args, function(){alert("Sent!");});
};

function togglePendingInvitations() {
    $("#pending-invitations").slideToggle();
};

function getPendingInvitations() {
    doAPI("getPendingInvitations", {},
          function (data) {
              $("#count-pending-invitations").text(data.length);
              var pending = $("#pending-invitations ul");
              pending.empty();
              for (var i=0; i<data.length; i++) {
                  var d = data[i];
                  var h = $('<li><a href="#"></a></li>')
                      .appendTo(pending)
                  ;
                  h.find("a")
                      .text(d.petname)
                      .data("invite-number", i)
                      .on("click",
                          function() {var i = $(this).data("invite-number");
                                      $("#pending-invite-"+i).slideToggle();})
                  ;
                  var details = $('<ul/>')
                      .appendTo(h)
                      .hide()
                      .attr("id", "pending-invite-"+i)
                  ;
                  details.append($('<li/>').text("Invitation Code: "+d.code));
                  details.append($('<li/>').text("Sent: "+d.sent));
                  details.append($('<li/>').text("Expires: "+d.expires));
              }
              if (data.length) {
                  $("#toggle-pending-invitations").slideDown();
                  $("#pending-invite-0").show();
              } else {
                  $("#toggle-pending-invitations").slideUp();
              }
          });
};

function startInvitation(event) {
    doAPI("startInvitation", {});
    $("#invite").slideUp(500);
    $("#invite-prepare-invitation").slideDown(500);
    $("#invite-to").focus(); // TODO: make 'return' trigger the button
};

function sendInvitation(event) {
    var args = { name: $("#invite-to").val() };
    doAPI("sendInvitation", args, getPendingInvitations);
    $("#pending-invitations").slideDown();
    $("#pending-invite-0").slideDown();
    $("#invite-prepare-invitation").slideUp();
    setTimeout(function() { $("#invite").slideDown("slow"); }, 5000);
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
                           else if (ui.index == 1) {
                               getPendingInvitations();
                           }
                           return true;
                       }
                       });
      $("#send-message").on("click", sendMessage);

      $("#toggle-pending-invitations").on("click", togglePendingInvitations);
      $("#invite input").on("click", startInvitation);
      $("#invite-cancel").on("click", function () {
                                 $("#invite").slideDown(500);
                                 $("#invite-prepare-invitation").slideUp(500);
                                 });
      $("#send-invitation").on("click", sendInvitation);
});
