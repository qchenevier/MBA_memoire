var gulp = require('gulp');
var exec = require('child_process').execSync;

var buildCommand = 'make'

gulp.task('default', ['watch']);

gulp.task('watch', function () {
  gulp.watch('*.md', ['build']);
});

gulp.task('build', function() {
  return exec(buildCommand, function(error, standardOutput, standardError) {
    if (error) {
      console.error('There was an error: ' + error);
    }
    console.log(standardOutput);
    console.log(standardError);
  });
});
