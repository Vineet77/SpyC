
(function() {

    let mallocLocation;
    let mallocSize

    function fctName(fctId) {
        const fct = Wasabi.module.info.functions[fctId];
        if (fct.export[0] !== undefined) return fct.export[0];
        if (fct.import !== null) return fct.import;
        return fctId;
    }

    Wasabi.analysis = {
        start(location) {
            console.log(location, "start");
        },

        call_pre(location, targetFunc, args, indirectTableIdx) {
            if (fctName(targetFunc) === "malloc") {
                mallocLocation = location;
                mallocSize = args[0];
                console.log('Call malloc');
            }
        },

        call_post(location, values) {
            if (mallocLocation !== undefined && mallocLocation.func == location.func && mallocLocation.instr == location.instr) {
                console.log(location, "malloc of size", mallocSize, "got address", values[0]);
                mallocLocation = undefined;
            }
        },
        
        load(location, op, memarg, value) {
            console.log(location, op, "value =", value, "from =", memarg);
        },

        store(location, op, memarg, value) {
            console.log(location, op, "value =", value, "to =", memarg);
        },

        memory_size(location, currentSizePages) {
            console.log(location, "memory_size, size (in pages) =", currentSizePages);
        },

        memory_grow(location, byPages, previousSizePages) {
            console.log(location, "memory_grow, delta (in pages) =", byPages, "previous size (in pages) =", previousSizePages);
        },

    };
})();