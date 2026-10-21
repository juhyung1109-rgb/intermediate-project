// Headless test of app.js functions
const fs = require('fs');

global.window = global;
const createMockElem = () => ({
  innerText: '',
  innerHTML: '',
  className: '',
  value: '',
  style: {},
  appendChild: () => {},
  classList: { add: () => {}, remove: () => {} },
  setAttribute: () => {}
});

global.document = {
  getElementById: (id) => createMockElem(),
  createElement: (tag) => createMockElem(),
  querySelectorAll: () => [],
  addEventListener: () => {}
};
global.showToast = () => {};

require('../web/data_cumulative_all.js');
let appCode = fs.readFileSync('web/app.js', 'utf-8');
appCode = appCode.replace('const state =', 'global.state = window.state =');
eval(appCode);

console.log("Testing getActiveDataset()...");
global.state.unifiedPeriod = '2008-11';
let ds1 = getActiveDataset();
console.log("2008-11 count:", ds1.totalCount, "scope:", ds1.scopeName);

global.state.unifiedPeriod = '2009-01';
let ds2 = getActiveDataset();
console.log("2009-01 count:", ds2.totalCount, "scope:", ds2.scopeName);

global.state.unifiedPeriod = '2009-08';
let ds3 = getActiveDataset();
console.log("2009-08 count:", ds3.totalCount, "scope:", ds3.scopeName);

console.log("Testing renderWafer for various months...");
renderWafer('1254'); // 2008-10
console.log("renderWafer(1254) passed!");

renderWafer('2050'); // 2008-11
console.log("renderWafer(2050) passed!");

renderWafer('2237'); // 2009-01
console.log("renderWafer(2237) passed!");

renderWafer('2595'); // 2009-04
console.log("renderWafer(2595) passed!");

renderWafer('3085'); // 2009-09
console.log("renderWafer(3085) passed!");

console.log("Testing setUnifiedGlobalPeriod...");
setUnifiedGlobalPeriod('2009-01');
console.log("setUnifiedGlobalPeriod(2009-01) passed! Selected wafer:", global.state.selectedWaferId);

setUnifiedGlobalPeriod('2008-11');
console.log("setUnifiedGlobalPeriod(2008-11) passed! Selected wafer:", global.state.selectedWaferId);

setUnifiedGlobalPeriod('2009-08');
console.log("setUnifiedGlobalPeriod(2009-08) passed! Selected wafer:", global.state.selectedWaferId);

console.log("ALL HEADLESS TESTS PASSED WITH 100% SUCCESS!");
