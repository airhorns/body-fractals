uniform float time;
uniform vec2 resolution;
uniform vec3 cameraPos;
uniform vec3 cameraLookat;
uniform vec3 lightDir;
uniform vec3 lightColour;
uniform vec3 diffuse;
uniform float ambientFactor;
uniform bool ao;
uniform bool shadows;
uniform bool rotateWorld;
uniform bool antialias;

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

float Plane(vec3 p, vec3 n)
{
   return dot(p, n);
}

// Formula for fractal from http://blog.hvidtfeldts.net/index.php/2011/08/distance-estimated-3d-fractals-iii-folding-space/
float Fractal(vec3 pos)
{
   const int Iterations = 30;
   const float Scale = 1.85;
   const float Offset = 2.0;

  vec3 a1 = vec3(1,1,1);
	vec3 a2 = vec3(-1,-1,1);
	vec3 a3 = vec3(1,-1,-1);
	vec3 a4 = vec3(-1,1,-1);
	vec3 c;
	float dist, d;
	for (int n = 0; n < Iterations; n++)
	{
      if(pos.x+pos.y<0.) pos.xy = -pos.yx; // fold 1
      if(pos.x+pos.z<0.) pos.xz = -pos.zx; // fold 2
      if(pos.y+pos.z<0.) pos.zy = -pos.yz; // fold 3
      pos = RotateY(pos, 0.05*PI);

      pos = pos*Scale - Offset*(Scale-1.0);
	}
	return length(pos) * pow(Scale, -float(Iterations));
}

// This should return continuous positive values when outside and negative values inside,
// which roughly indicate the distance of the nearest surface.
float Dist(vec3 pos)
{
   if (rotateWorld) pos = RotateY(pos, sin(time)*0.5);

   return min(
      Plane(pos-vec3(0.,-2.0,0.), vec3(0.,1.,0.)),
      Fractal(pos)
   );
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

// Based on original code by IQ
float SoftShadow(vec3 ro, vec3 rd, float k)
{
   float res = 1.0;
   float t = 0.01;          // min-t see http://www.iquilezles.org/www/articles/rmshadows/rmshadows.htm
   for (int i=0; i<SHADOW_RAY_DEPTH; i++)
   {
      if (t < 25.0)  // max-t
      {
         float h = Dist(ro + rd * t);
         res = min(res, k*h/t);
         t += h;
      }
   }
   return clamp(res, 0.0, 1.0);
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
   if (shadows) light *= SoftShadow(pos, lightDir, 32.0);
   if (ao) light += CalcAO(pos, norm) * ambientFactor;
   return vec4(light, 1.0);
}

// Original method by David Hoskins
vec3 Sky(in vec3 rd)
{
   float sunAmount = max(dot(rd, lightDir), 0.0);
   float v = pow(1.0 - max(rd.y,0.0),6.);
   vec3 sky = mix(vec3(.1, .2, .3), vec3(.32, .32, .32), v);
   sky += lightColour * sunAmount * sunAmount * .25 + lightColour * min(pow(sunAmount, 800.0)*1.5, .3);

   sky = vec3(sin(time), cos(time), 1);
   return clamp(sky, 0.0, 1.0);
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

   if (antialias)
   {
      float d_ang = 2.*PI / float(ANTIALIAS_SAMPLES);
      float ang = d_ang * 0.33333;
      float r = 0.3;
      for (int i = 0; i < ANTIALIAS_SAMPLES; i++)
      {
         vec2 p = vec2((gl_FragCoord.x + cos(ang)*r) / resolution.x, (gl_FragCoord.y + sin(ang)*r) / resolution.y);
         vec3 ro = cameraPos;
         vec3 rd = normalize(GetRay(cameraLookat-cameraPos, p));
         vec4 _res = March(ro, rd);
         if (_res.a == 1.0) res.xyz += clamp(Shading(_res.xyz, rd, GetNormal(_res.xyz)).xyz, 0.0, 1.0);
         else res.xyz += Sky(rd);
         ang += d_ang;
      }
      res.xyz /= float(ANTIALIAS_SAMPLES);
   }
   else
   {
      vec2 p = gl_FragCoord.xy / resolution.xy;
      vec3 ro = cameraPos;
      vec3 rd = normalize(GetRay(cameraLookat-cameraPos, p));
      res = March(ro, rd);
      if (res.a == 1.0) res.xyz = clamp(Shading(res.xyz, rd, GetNormal(res.xyz)).xyz, 0.0, 1.0);
      else res.xyz = Sky(rd);
   }

   gl_FragColor = vec4(res.xyz, 1.0);
}
