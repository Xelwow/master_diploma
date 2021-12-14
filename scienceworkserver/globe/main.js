require([
    "esri/Map",
    "esri/views/SceneView",
    "esri/layers/GeoJSONLayer",
    "dojo/domReady!" // will not be called until DOM is ready
], function (
    Map,
    SceneView,
    GeoJSONLayer
) {
    renderer = {
        type: "unique-value",
        defaultSymbol: {
            type: "line-3d",
            symbolLayers: [{
                type: "line",
                outline: {color: [255, 84, 54, 0.6], size: 10, width: 2},
                join: "round"
            }]
        },
        visualVariables: [
            {
                type: "size",
                field: "title",
                stops: [
                    {value: 4, size: 1},
                    {value: 100, size: 1}
                ]
            },
            {
                type: "color",
                field: "title",
                legendOptions: {
                    title: "Prob., %"
                },
                //#5813fc,#1cc2fd,#7dfd94,#f5c926,#ff2b18
                stops: [
                    {
                        value: 5,
                        color: "#5813fc",
                        label: "0",
                    },
                    {
                        value: 10,
                        color: "#1cc2fd",
                    },
                    {
                        value: 20,
                        color: "#7dfd94",
                    },
                    {
                        value: 40,
                        color: "#f5c926",
                    },
                    {
                        value: 100,
                        color: "#ff2b18",
                        label: " 100",
                    }
                ]

            }
        ]
    };
    popupTemplate = {
        title: "Aurora Probability",
        content: "{title}"
    };
    const geoJSONLayer = new GeoJSONLayer({
        url: 'http://127.0.0.1:8000/geodata/get/',
        popupEnabled: true,
        outFields: ["title"],
        popupTemplate: popupTemplate,
        renderer: renderer,
        highlightOptions: {
            haloOpacity: 0.9,
            fillOpacity: 0.2
        },
        elevationInfo: {
            mode: 'relative-to-scene'
        }
    });
    geoJSONLayer.opacity = 1;

    const map = new Map({
        basemap: 'satellite'
    });

    map.add(geoJSONLayer);

    const view = new SceneView({
        map: map,
        container: "sceneContainer",
    });
});

