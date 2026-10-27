import java.io.File;
import java.lang.reflect.InvocationTargetException;

/** Calls the official installer's public entry point, using our game directory. */
public class OptiFineBridge {
    public static void main(String[] args) throws Exception {
        Class<?> installer = Class.forName("optifine.Installer");
        if (args[0].equals("version")) {
            String version = (String) installer.getMethod("getOptiFineVersion").invoke(null);
            System.out.println(installer.getMethod("getMinecraftVersionFromOfVersion", String.class).invoke(null, version));
            return;
        }
        try {
            installer.getMethod("doInstall", File.class).invoke(null, new File(args[0]));
        } catch (InvocationTargetException e) {
            throw new Exception("OptiFine installation failed", e.getCause());
        }
    }
}
