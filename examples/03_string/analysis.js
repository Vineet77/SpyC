let mallocLocation;
let mallocSize;
let mallocs = [];
let prevMallocStores = [];

function getNextAddr(op, addr) {
    switch (op) {
        case "i32.store":
            return addr + 4;
        case "i32.store8":
            return addr + 1;
    }
    return addr + 4; //default
}


function analyizeMallocHistoy() {
    const begin = prevMallocStores[0].addr;
    const lastMallocStore = prevMallocStores[prevMallocStores.length - 1]
    const end = getNextAddr(lastMallocStore.op, lastMallocStore.addr);
    const mallocRegion = mallocs.find(m => begin >= m.addr && begin <= m.addr);
    console.log("Potential buffer overflow. Continuous allocation of size", end - begin, "at", begin, "overflowing malloc region at",  mallocRegion.addr, "of size", mallocRegion.size);
}


(function () {


    function updateMallocHistory(op, addr, inMallocRegion) {
        if (prevMallocStores.length === 0) {
            if (inMallocRegion) prevMallocStores.push({ op, addr })

            return;
        } else {
            const lastStore = prevMallocStores[prevMallocStores.length - 1];
            const endAddr = getNextAddr(lastStore.op, lastStore.addr);
            //check is addr is the next addr to be loaded
            if (endAddr === addr) {
                prevMallocStores.push({ op, addr });
            } else { //reset the malloc history
                analyizeMallocHistoy();
                prevMallocStores = inMallocRegion ? [{ op, addr }] : []
            }
        }
    }

    function fctName(fctId) {
        const fct = Wasabi.module.info.functions[fctId];
        if (fct.export[0] !== undefined) return fct.export[0];
        if (fct.import !== null) return fct.import;
        return fctId;
    }

    function inSequenceStore(op, addr) {
        if (prevMallocStore === null) return false;
        if (op !== prevMallocStore.op) return false;
    }


    Wasabi.analysis = {
        start(location) {
            console.log(location, "start");
        },

        call_pre(location, targetFunc, args, indirectTableIdx) {
            if (fctName(targetFunc) === "malloc") {
                mallocLocation = location;
                mallocSize = args[0];
            }
        },

        call_post(location, values) {
            if (mallocLocation !== undefined && mallocLocation.func == location.func && mallocLocation.instr == location.instr) {
                console.log("malloc call of size", mallocSize, "got address", values[0]);
                mallocs.push({ addr: values[0], size: mallocSize });
                mallocLocation = undefined;
            }
        },

        // load(location, op, memarg, value) {
        //     console.log(location, op, "value =", value, "from =", memarg);
        // },

        store(location, op, memarg, value) {
            let { addr, offset } = memarg;
            effectiveAddr = addr + offset;
            let mallocRegion = null;
            for (malloc of mallocs) {
                if (effectiveAddr >= malloc.addr && effectiveAddr <= malloc.addr + malloc.size) {
                    mallocRegion = malloc;
                    break;
                }
            }
            if (mallocRegion !== null) {
                console.log(op, "of value", "0x" + value.toString(16), "happened at",  effectiveAddr, "in malloced region at addr",  mallocRegion.addr, "of size", mallocRegion.size);
                updateMallocHistory(op, effectiveAddr, true);
            } else {
                console.log(op, "of value", "0x" + value.toString(16), "happened at", effectiveAddr);
                updateMallocHistory(op, effectiveAddr, false);
            }

        },

    };
})();