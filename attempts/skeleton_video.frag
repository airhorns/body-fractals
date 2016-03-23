uniform vec2 resolution;
uniform sampler2D frame;


void main()
{
  vec2 p = gl_FragCoord.xy / resolution.xy;
  vec3 absoluteDepth = texture2D(frame, p).aaa * pow(2, 8) + texture2D(frame, p).bbb;
  gl_FragColor = vec4(absoluteDepth / pow(2.0, 4), 1.0);
}
