## 说明
配置类处理器
- 处理@Component注解类，注册为BeanDefinition
- 处理@Configuration注解类，注册为BeanDefinition
- 处理@Import注解类
- 处理实现ImportSelector接口方式的类，执行注册BeanDefinition的方法
  - SpringBoot的自动装配AutoConfigurationImportSelector使用的是ImportSelector接口方式

> configCandidates实际上就是SprivalApplication

```java
public class ConfigurationClassPostProcessor implements BeanDefinitionRegistryPostProcessor,
        PriorityOrdered, ResourceLoaderAware, BeanClassLoaderAware, EnvironmentAware {
    
    public void processConfigBeanDefinitions(BeanDefinitionRegistry registry) {
        List<BeanDefinitionHolder> configCandidates = new ArrayList<>();
        
        // registry => sprivalApplication的beanFactory
        // 6个RootBeenDefinition和自身 sprivalApplication
        String[] candidateNames = registry.getBeanDefinitionNames();

        for (String beanName : candidateNames) {
            BeanDefinition beanDef = registry.getBeanDefinition(beanName);
            if (beanDef.getAttribute(ConfigurationClassUtils.CONFIGURATION_CLASS_ATTRIBUTE) != null) {
                if (logger.isDebugEnabled()) {
                    logger.debug("Bean definition has already been processed as a configuration class: " + beanDef);
                }
            } else if (ConfigurationClassUtils.checkConfigurationClassCandidate(beanDef, this.metadataReaderFactory)) {
                // 筛选出sprivalApplication
                configCandidates.add(new BeanDefinitionHolder(beanDef, beanName));
            }
        }

        // Return immediately if no @Configuration classes were found
        if (configCandidates.isEmpty()) {
            return;
        }

        // Sort by previously determined @Order value, if applicable
        configCandidates.sort((bd1, bd2) -> {
            int i1 = ConfigurationClassUtils.getOrder(bd1.getBeanDefinition());
            int i2 = ConfigurationClassUtils.getOrder(bd2.getBeanDefinition());
            return Integer.compare(i1, i2);
        });

        // Detect any custom bean name generation strategy supplied through the enclosing application context
        SingletonBeanRegistry sbr = null;
        if (registry instanceof SingletonBeanRegistry) {
            sbr = (SingletonBeanRegistry) registry;
            if (!this.localBeanNameGeneratorSet) {
                BeanNameGenerator generator = (BeanNameGenerator) sbr.getSingleton(
                        AnnotationConfigUtils.CONFIGURATION_BEAN_NAME_GENERATOR);
                if (generator != null) {
                    this.componentScanBeanNameGenerator = generator;
                    this.importBeanNameGenerator = generator;
                }
            }
        }

        if (this.environment == null) {
            this.environment = new StandardEnvironment();
        }

        // Parse each @Configuration class
        ConfigurationClassParser parser = new ConfigurationClassParser(
                this.metadataReaderFactory, this.problemReporter, this.environment,
                this.resourceLoader, this.componentScanBeanNameGenerator, registry);

        Set<BeanDefinitionHolder> candidates = new LinkedHashSet<>(configCandidates);
        Set<ConfigurationClass> alreadyParsed = new HashSet<>(configCandidates.size());
        do {
            // 
            parser.parse(candidates);
            parser.validate();

            Set<ConfigurationClass> configClasses = new LinkedHashSet<>(parser.getConfigurationClasses());
            configClasses.removeAll(alreadyParsed);

            // Read the model and create bean definitions based on its content
            if (this.reader == null) {
                this.reader = new ConfigurationClassBeanDefinitionReader(
                        registry, this.sourceExtractor, this.resourceLoader, this.environment,
                        this.importBeanNameGenerator, parser.getImportRegistry());
            }
            this.reader.loadBeanDefinitions(configClasses);
            alreadyParsed.addAll(configClasses);

            candidates.clear();
            if (registry.getBeanDefinitionCount() > candidateNames.length) {
                String[] newCandidateNames = registry.getBeanDefinitionNames();
                Set<String> oldCandidateNames = new HashSet<>(Arrays.asList(candidateNames));
                Set<String> alreadyParsedClasses = new HashSet<>();
                for (ConfigurationClass configurationClass : alreadyParsed) {
                    alreadyParsedClasses.add(configurationClass.getMetadata().getClassName());
                }
                for (String candidateName : newCandidateNames) {
                    if (!oldCandidateNames.contains(candidateName)) {
                        BeanDefinition bd = registry.getBeanDefinition(candidateName);
                        if (ConfigurationClassUtils.checkConfigurationClassCandidate(bd, this.metadataReaderFactory) &&
                                !alreadyParsedClasses.contains(bd.getBeanClassName())) {
                            candidates.add(new BeanDefinitionHolder(bd, candidateName));
                        }
                    }
                }
                candidateNames = newCandidateNames;
            }
        }
        while (!candidates.isEmpty());

        // Register the ImportRegistry as a bean in order to support ImportAware @Configuration classes
        if (sbr != null && !sbr.containsSingleton(IMPORT_REGISTRY_BEAN_NAME)) {
            sbr.registerSingleton(IMPORT_REGISTRY_BEAN_NAME, parser.getImportRegistry());
        }

        if (this.metadataReaderFactory instanceof CachingMetadataReaderFactory) {
            // Clear cache in externally provided MetadataReaderFactory; this is a no-op
            // for a shared cache since it'll be cleared by the ApplicationContext.
            ((CachingMetadataReaderFactory) this.metadataReaderFactory).clearCache();
        }
    }
}
```

















## 

执行 AutoConfigurationImportSelector 类的地方

```text
getAutoConfigurationEntry:122, AutoConfigurationImportSelector (org.springframework.boot.autoconfigure)
 :434, AutoConfigurationImportSelector$AutoConfigurationGroup (org.springframework.boot.autoconfigure)
getImports:879, ConfigurationClassParser$DeferredImportSelectorGrouping (org.springframework.context.annotation)
processGroupImports:809, ConfigurationClassParser$DeferredImportSelectorGroupingHandler (org.springframework.context.annotation)
process:780, ConfigurationClassParser$DeferredImportSelectorHandler (org.springframework.context.annotation)
parse:193, ConfigurationClassParser (org.springframework.context.annotation)
processConfigBeanDefinitions:320, ConfigurationClassPostProcessor (org.springframework.context.annotation)
postProcessBeanDefinitionRegistry:237, ConfigurationClassPostProcessor (org.springframework.context.annotation)
invokeBeanDefinitionRegistryPostProcessors:280, PostProcessorRegistrationDelegate (org.springframework.context.support)
invokeBeanFactoryPostProcessors:96, PostProcessorRegistrationDelegate (org.springframework.context.support)
invokeBeanFactoryPostProcessors:707, AbstractApplicationContext (org.springframework.context.support)
refresh:533, AbstractApplicationContext (org.springframework.context.support)
refresh:143, ServletWebServerApplicationContext (org.springframework.boot.web.servlet.context)
refresh:755, SpringApplication (org.springframework.boot)
refresh:747, SpringApplication (org.springframework.boot)
refreshContext:402, SpringApplication (org.springframework.boot)
run:312, SpringApplication (org.springframework.boot)
main:18, SprivalApplication (com.soyokra.sprival)
```



ImportBeanDefinitionRegistrar.registerBeanDefinitions
```text
registerBeanDefinitions:60, AutoProxyRegistrar (org.springframework.context.annotation)
registerBeanDefinitions:86, ImportBeanDefinitionRegistrar (org.springframework.context.annotation)
lambda$loadBeanDefinitionsFromRegistrars$1:384, ConfigurationClassBeanDefinitionReader (org.springframework.context.annotation)
accept:-1, 2096194236 (org.springframework.context.annotation.ConfigurationClassBeanDefinitionReader$$Lambda$244)
forEach:684, LinkedHashMap (java.util)
loadBeanDefinitionsFromRegistrars:383, ConfigurationClassBeanDefinitionReader (org.springframework.context.annotation)
loadBeanDefinitionsForConfigurationClass:148, ConfigurationClassBeanDefinitionReader (org.springframework.context.annotation)
loadBeanDefinitions:120, ConfigurationClassBeanDefinitionReader (org.springframework.context.annotation)
processConfigBeanDefinitions:332, ConfigurationClassPostProcessor (org.springframework.context.annotation)
postProcessBeanDefinitionRegistry:237, ConfigurationClassPostProcessor (org.springframework.context.annotation)
invokeBeanDefinitionRegistryPostProcessors:280, PostProcessorRegistrationDelegate (org.springframework.context.support)
invokeBeanFactoryPostProcessors:96, PostProcessorRegistrationDelegate (org.springframework.context.support)
invokeBeanFactoryPostProcessors:707, AbstractApplicationContext (org.springframework.context.support)
refresh:533, AbstractApplicationContext (org.springframework.context.support)
refresh:143, ServletWebServerApplicationContext (org.springframework.boot.web.servlet.context)
refresh:755, SpringApplication (org.springframework.boot)
refresh:747, SpringApplication (org.springframework.boot)
refreshContext:402, SpringApplication (org.springframework.boot)
run:312, SpringApplication (org.springframework.boot)
main:18, SprivalApplication (com.soyokra.sprival)
```