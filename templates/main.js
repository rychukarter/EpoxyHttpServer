$(document).ready(function () {
    console.log($.ajax);

    $("#btn-start-client").click(function(){
        $.ajax({
            type: "POST",
            url: "/services/start-client",
            data: JSON.stringify({ "clientID": $("#clientId").val()}),
            contentType : 'application/json',
            success: function(msg){
                    document.getElementById("success-info").innerHTML = "Client (id"+$("#clientId").val() +") started";
            },
            error: function(){
                     document.getElementById("fail-info").innerHTML = "Client did not start";
            }
        });
    });


    $("#btn-stop-client").click(function(){
        $.ajax({
            type: "POST",
            url: "/services/stop-client",
            data: JSON.stringify({ "clientID": $("#clientId").val()}),
            contentType : 'application/json',
            success: function(msg){
                    document.getElementById("success-info").innerHTML = "Client (id"+$("#clientId").val() +") stopped";
            },
            error: function(){
                     document.getElementById("fail-info").innerHTML = "Client did not stop";
            }
        });
    });

   $("#btn-connect-client").click(function(){
        $.ajax({
            type: "POST",
            url: "/services/connect-client",
            data: JSON.stringify({ "clientID": $("#clientId").val(), "ip": $("#ServerIp").val(), "port": $("#ServerPort").val()}),
            contentType : 'application/json',
            success: function(msg){
                    document.getElementById("success-info").innerHTML = "Client (id"+$("#clientId").val() +") connected";
            },
            error: function(){
                     document.getElementById("fail-info").innerHTML = "Client did not connect";
            }
        });
    });

    $("#btn-disconnect-client").click(function(){
        $.ajax({
            type: "POST",
            url: "/services/disconnect-client",
            data: JSON.stringify({ "clientID": $("#clientId").val()}),
            contentType : 'application/json',
            success: function(msg){
                    document.getElementById("success-info").innerHTML = "Client (id"+$("#clientId").val() +") disconnected";
            },
            error: function(){
                     document.getElementById("fail-info").innerHTML = "Client did not disconnected";
            }
        });
    });

    $("#btn-start-calibration").click(function(){
        $.ajax({
            type: "POST",
            url: "/services/start-calibration",
            data: JSON.stringify({ "clientID": $("#clientId").val(), "calibrationChannel": $("#CalibrationChannel").val(), "calibrationResistance": $("#CalibrationResistance").val(), "calibrationFrequency": $("#CalibrationFrequency").val(), "calibrationPhase": $("#CalibrationPhase").val()}),
            contentType : 'application/json',
            success: function(msg){
                    document.getElementById("success-info").innerHTML = "Client (id"+$("#clientId").val() +") stopped";
            },
            error: function(){
                     document.getElementById("fail-info").innerHTML = "Client did not stop";
            }
        });
    });

    $("#btn-start-measurement").click(function(){
        $.ajax({
            type: "POST",
            url: "/services/start-measurement",
            data: JSON.stringify({ "clientID": $("#clientId").val(), "measurementFrequency": $("#MeasurementFrequency").val(), "timeBetween": $("#TimeBetween").val(), "measurementNumber": $("#MeasurementNumber").val(), "channelNumber": $("#ChannelNumber").val()}),
            contentType : 'application/json',
            success: function(msg){
                    document.getElementById("success-info").innerHTML = "Client (id"+$("#clientId").val() +") stopped";
            },
            error: function(){
                     document.getElementById("fail-info").innerHTML = "Client did not stop";
            }
        });
    });

    $("#btn-stop-measurement").click(function(){
        $.ajax({
            type: "POST",
            url: "/services/stop-measurement",
            data: JSON.stringify({ "clientID": $("#clientId").val()}),
            contentType : 'application/json',
            success: function(msg){
                    document.getElementById("success-info").innerHTML = "Client (id"+$("#clientId").val() +") stopped";
            },
            error: function(){
                     document.getElementById("fail-info").innerHTML = "Client did not stop";
            }
        });
    });
});

function formSuccess() {
}
