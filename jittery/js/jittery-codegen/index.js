
var util = require('util')

var escodegen = require('escodegen');

process.stdin.resume();
process.stdin.setEncoding('utf8');

var astJson = '';
process.stdin.on('data', function(chunk) {
  astJson += chunk;
});

process.stdin.on('end', function() {
  var parsedJson, code;
  try {
    parsedJson = JSON.parse(astJson);
    code = escodegen.generate(parsedJson, {
      format: {
        indent: {
          style: '  '
        }
      }
    });
  } catch (e) {
    if (parsedJson) {
      console.error(util.inspect(parsedJson, {depth: 100, colors: true}));
    }
    throw e;
  }
  console.log(code);
});
