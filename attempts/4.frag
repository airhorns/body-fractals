uniform float time;
uniform vec2 resolution;
uniform vec3 cameraPos;
uniform vec3 cameraLookat;
uniform vec3 lightDir;
uniform vec3 lightColour;
uniform vec3 diffuse;
uniform float ambientFactor;
uniform bool rotateWorld;
uniform bool antialias;
uniform float scale;
uniform float offset;
uniform float cubeWidth;

#define PI 3.14159265
#define GAMMA 0.8
#define AO_SAMPLES 5
#define RAY_DEPTH 256
#define MAX_DEPTH 100.0
#define SHADOW_RAY_DEPTH 32
#define DISTANCE_MIN 0.01

const vec2 delta = vec2(DISTANCE_MIN, 0.);


vec3 RotateY(vec3 p, float a)
{
   float c,s;
   vec3 q=p;
   c = cos(a);
   s = sin(a);
   p.x = c * q.x + s * q.z;
   p.z = -s * q.x + c * q.z;
   return p;
}

vec2 rotate(vec2 v, float a) {
	return vec2(cos(a)*v.x + sin(a)*v.y, -sin(a)*v.x + cos(a)*v.y);
}

float trap(vec3 p){
	// return  length(p.x-1.0); // unit cube
	// return  length(p.x-cubeWidth; // <- cube forms
  return  length(p.x-0.5-0.5*sin(time/10.0)); // <- cube forms
	// return length(p.xz-vec2(1.0,1.0))-0.05; // <- tube forms
	// return length(p); // <- no trap
}

float Plane(vec3 p, vec3 n)
{
   return dot(p, n);
}

// from https://www.shadertoy.com/view/XsX3z7
float Fractal(in vec3 z)
{
  const int Iterations = 14;

	float d = 1000.0;
	float r;
	for (int n = 0; n < Iterations; n++) {
		z.xz = rotate(z.xz, time/18.0);

		// This is octahedral symmetry,
		// with some 'abs' functions thrown in for good measure.
		if (z.x+z.y<0.0) z.xy = -z.yx;
		z = abs(z);
		if (z.x+z.z<0.0) z.xz = -z.zx;
		z = abs(z);
		if (z.x-z.y<0.0) z.xy = z.yx;
		z = abs(z);
		if (z.x-z.z<0.0) z.xz = z.zx;
		z = z*scale - offset*(scale-1.0);
		z.yz = rotate(z.yz, -time/18.0);

		d = min(d, trap(z) * pow(scale, -float(n+1)));
	}
	return d;
}


// This should return continuous positive values when outside and negative values inside,
// which roughly indicate the distance of the nearest surface.
float Dist(vec3 pos)
{
   if (rotateWorld) pos = RotateY(pos, time*0.025);

   return Fractal(pos);
  //  return min(
  //     Plane(pos-vec3(0.,-2.0,0.), vec3(0.,1.,0.)),
  //     Fractal(pos)
  //  );
}

// Based on original by IQ - optimized to remove a divide
float CalcAO(vec3 p, vec3 n)
{
   float r = 0.0;
   float w = 1.0;
   for (int i=1; i<=AO_SAMPLES; i++)
   {
      float d0 = float(i) * 0.3;
      r += w * (d0 - Dist(p + n * d0));
      w *= 0.5;
   }
   return 1.0 - clamp(r,0.0,1.0);
}

vec3 GetNormal(vec3 pos)
{
   vec3 n;
   n.x = Dist( pos + delta.xyy ) - Dist( pos - delta.xyy );
   n.y = Dist( pos + delta.yxy ) - Dist( pos - delta.yxy );
   n.z = Dist( pos + delta.yyx ) - Dist( pos - delta.yyx );

   return normalize(n);
}

// Based on a shading method by Ben Weston. Added AO and SoftShadows to original.
vec4 Shading(vec3 pos, vec3 rd, vec3 norm)
{
   vec3 light = lightColour * max(0.0, dot(norm, lightDir));
   vec3 heading = normalize(-rd + lightDir);

   light = (diffuse * light);
   light += CalcAO(pos, norm) * ambientFactor;
   return vec4(light, 1.0);
}

// Camera function by TekF
// Compute ray from camera parameters
vec3 GetRay(vec3 dir, vec2 pos)
{
   pos = pos - 0.5;
   pos.x *= resolution.x/resolution.y;

   dir = normalize(dir);
   vec3 right = normalize(cross(vec3(0.,1.,0.),dir));
   vec3 up = normalize(cross(dir,right));

   return dir + right*pos.x + up*pos.y;
}

vec4 March(vec3 ro, vec3 rd)
{
   float t = 0.0;
   float d = 1.0;
   for (int i=0; i<RAY_DEPTH; i++)
   {
      vec3 p = ro + rd * t;
      d = Dist(p);
      if (abs(d) < DISTANCE_MIN)
      {
         return vec4(p, 1.0);
      }
      t += d;
      if (t >= MAX_DEPTH) break;
   }
   return vec4(0.0);
}

void main()
{
  const int ANTIALIAS_SAMPLES = 4;

  vec4 res = vec4(0.0);

  float d_ang = 2.*PI / float(ANTIALIAS_SAMPLES);
  float ang = d_ang * 0.33333;
  float r = 0.3;
  for (int i = 0; i < ANTIALIAS_SAMPLES; i++) {
     vec2 p = vec2((gl_FragCoord.x + cos(ang)*r) / resolution.x, (gl_FragCoord.y + sin(ang)*r) / resolution.y);
     vec3 ro = cameraPos;
     vec3 rd = normalize(GetRay(cameraLookat-cameraPos, p));
     vec4 _res = March(ro, rd);
     if (_res.a == 1.0) {
        res.xyz += clamp(Shading(_res.xyz, rd, GetNormal(_res.xyz)).xyz, 0.0, 1.0);
     } else {
        res.xyz = vec3(0.49, 0.5, 0.51);  // a nice grey to match my terminal
     }
     ang += d_ang;
  }

  res.xyz /= float(ANTIALIAS_SAMPLES);

  gl_FragColor = vec4(res.xyz, 1.0);
}
