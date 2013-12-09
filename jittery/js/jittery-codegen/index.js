
var escodegen = require('escodegen');

process.stdin.resume();
process.stdin.setEncoding('utf8');

var astJson = '';
process.stdin.on('data', function(chunk) {
  astJson += chunk;
});

process.stdin.on('end', function() {
  console.log(escodegen.generate(JSON.parse(astJson)));
});
